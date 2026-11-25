#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import collections
import dataclasses
import json
import os
import pathlib
import re
import socket
import subprocess
import time
import typing
import xml.etree.ElementTree as ET

FILENAME_REGEX = re.compile(r"^SENSOR_MODULE_CH_QCQA\.(?P<barcode>\d+)\.xml$")


@dataclasses.dataclass
class ModuleInfo:
    xml_path: str
    xml_barcode: str
    xml_version: str
    db_barcode: typing.Optional[str] = None
    db_versions: list[str] = dataclasses.field(default_factory=list)
    db_latest_version: typing.Optional[str] = None
    version_conflict: bool = False
    xml_version_lt_latest: bool = False


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter,
):
    pass


def natural_sort(values: list[str]) -> list[str]:
    return sorted(values, key=natural_sort_key)


def natural_sort_key(value: str) -> list[typing.Union[int, str]]:
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"([0-9]+)", value)]


def compare_natural_values(left: str, right: str) -> int:
    left_key = natural_sort_key(left)
    right_key = natural_sort_key(right)
    if left_key < right_key:
        return -1
    if left_key > right_key:
        return 1
    return 0


def is_tunnel_open(port: int = 8113) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


def run_db_query(query: str, port: int = 8113) -> dict[str, typing.Any]:
    assert is_tunnel_open(port=port), "Open tunnel to database first."

    tries = 0
    while tries < 5:
        try:
            dbquery_output = subprocess.run(
                [
                    "./python/rhapi.py",
                    "-u",
                    f"http://localhost:{port}",
                    "-a",
                    "-f",
                    "json2",
                    query,
                ],
                stdout=subprocess.PIPE,
                check=True,
            )
            output_str = dbquery_output.stdout.decode("utf-8").strip()
            try:
                payload = json.loads(output_str)
            except json.JSONDecodeError:
                payload = ast.literal_eval(output_str)

            if not isinstance(payload, dict):
                raise ValueError(f"Unexpected DB response type: {type(payload)}")
            if "data" not in payload:
                raise KeyError("Missing 'data' in DB response payload.")

            return payload
        except subprocess.CalledProcessError:
            tries += 1
            if tries >= 5:
                raise
            time.sleep(3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=Formatter,
        description=(
            "Scan directories for SENSOR_MODULE_CH_QCQA XML files, query existing "
            "module versions from DB, and summarize required version updates."
        ),
    )
    parser.add_argument(
        "--srcs",
        nargs="+",
        required=True,
        help="Directory path(s) to scan recursively for XML files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-module details in addition to summary.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print subprocess stdout/stderr from upload checks.",
    )
    parser.add_argument(
        "--database",
        type=str,
        choices=["mtd_int2r", "mtd_cmsr"],
        default="mtd_int2r",
        help="Database schema to query: mtd_int2r is test database, mtd_cmsr is the main database.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8113,
        help="Local port to query.",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload modules not found in the database or whose XML version is newer than the database version.",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=3,
        help="Number of retries for failed scp and remote-log checks.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="logs/upload_db",
        help="Directory to store upload results and module lists.",
    )
    parser.add_argument(
        "--modules",
        help="Only process this space-delimited list of modules (or files with a barcode per line), unless it is in --skipmodules.",
        type=str,
        nargs="+",
        required=False,
        default=[],
    )
    parser.add_argument(
        "--skipmodules",
        help="Space-delimited list of modules (or files with a barcode per line) to skip.",
        type=str,
        nargs="+",
        required=False,
        default=[],
    )
    return parser.parse_args()


def find_xml_files(directories: list[str]) -> list[pathlib.Path]:
    xml_files: list[pathlib.Path] = []

    for directory in directories:
        path = pathlib.Path(directory).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Directory does not exist: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        for xml_path in path.rglob("*.xml"):
            if FILENAME_REGEX.match(xml_path.name):
                xml_files.append(xml_path)

    return xml_files


def expand_module_filters(values: list[str]) -> set[str]:
    allowed: set[str] = set()

    for value in values:
        if os.path.isfile(value):
            with open(value, "r", encoding="utf-8") as fopen:
                for line in fopen:
                    barcode = line.strip()
                    if barcode:
                        allowed.add(barcode)
        else:
            allowed.add(value.strip())

    return allowed


def read_xml_version(xml_path: pathlib.Path) -> str:
    root = ET.parse(xml_path).getroot()
    version_node = root.find("./DATA_SET/VERSION")
    if version_node is None or version_node.text is None:
        raise ValueError(f"Missing DATA_SET/VERSION in XML: {xml_path}")

    version = version_node.text.strip()
    if not version:
        raise ValueError(f"Empty DATA_SET/VERSION in XML: {xml_path}")

    return version


def get_row_value_ci(row: dict, key: str) -> typing.Any:
    key_lower = key.lower()
    for row_key, row_value in row.items():
        if str(row_key).lower() == key_lower:
            return row_value
    return None


def chunked(values: list[str], chunk_size: int) -> list[list[str]]:
    return [values[idx: idx + chunk_size] for idx in range(0, len(values), chunk_size)]


def query_module_versions_bulk(
    barcodes: list[str],
    database: str,
    port: int = 8113,
    chunk_size: int = 500,
) -> dict[str, list[str]]:
    versions_by_barcode: dict[str, list[str]] = {barcode: [] for barcode in barcodes}

    for barcode_group in chunked(barcodes, chunk_size):
        barcode_group_sql = str(tuple(barcode_group)).replace(",)", ")")
        query = (
            "select s.part_barcode, c.VERSION "
            f"from {database}.c3420 s "
            f"JOIN {database}.datasets c on c.ID = s.CONDITION_DATA_SET_ID "
            f"where s.part_barcode in {barcode_group_sql} "
            "GROUP BY s.part_barcode, c.VERSION"
        )
        payload = run_db_query(query, port=port)
        rows = payload["data"]

        for row in rows:
            row_barcode = get_row_value_ci(row, "part_barcode")
            if row_barcode is None:
                row_barcode = get_row_value_ci(row, "partBarcode")
            if row_barcode is None:
                continue

            row_barcode_str = str(row_barcode)
            if row_barcode_str not in versions_by_barcode:
                continue

            row_version = get_row_value_ci(row, "version")
            if row_version is not None:
                versions_by_barcode[row_barcode_str].append(str(row_version))

    for barcode, versions in versions_by_barcode.items():
        versions_by_barcode[barcode] = natural_sort(list(set(versions)))

    return versions_by_barcode


DATABASE_SUFFIX_MAP = {
    "mtd_int2r": "int2r",
    "mtd_cmsr": "cmsr",
}


def get_database_upload_suffix(database: str) -> str:
    try:
        return DATABASE_SUFFIX_MAP[database]
    except KeyError as exc:
        raise ValueError(f"Unsupported database name: {database}") from exc


def select_modules_for_upload(modules: list[ModuleInfo]) -> list[ModuleInfo]:
    upload_modules: list[ModuleInfo] = []
    for module in modules:
        if module.db_barcode is None:
            upload_modules.append(module)
            continue
        if module.version_conflict or module.xml_version_lt_latest:
            continue
        if module.db_latest_version is None:
            continue
        if compare_natural_values(module.xml_version, module.db_latest_version) > 0:
            upload_modules.append(module)
    return upload_modules


def print_process_output(label: str, output: str) -> None:
    trimmed = (output or "").strip()
    if not trimmed:
        return
    print(f"{label}:")
    for line in trimmed.splitlines():
        print(f"{line}")


def run_scp_upload(module: ModuleInfo, database: str, retries: int, outdir: str, debug: bool = False) -> None:
    remote_db = get_database_upload_suffix(database)
    remote_target = f"mtd@dbloader-mtd.cern.ch:/home/dbspool/spool/mtd/{remote_db}/"
    scp_command = [
        "scp",
        "-o",
        f"ControlPath={os.path.expanduser('~/.ssh/socket_dbloader-mtd')}",
        str(module.xml_path),
        remote_target,
    ]

    last_error = ""
    for attempt in range(1, retries + 1):
        print(f"SCP attempt {attempt}/{retries} for {module.xml_barcode}")
        try:
            result = subprocess.run(
                scp_command,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(f"SCP succeeded for {module.xml_barcode} on attempt {attempt}/{retries}")
                break
            last_error = result.stderr.strip() or result.stdout.strip() or f"scp exited with code {result.returncode}"
            print_process_output("scp stdout", result.stdout)
            print_process_output("scp stderr", result.stderr)
            print(f"SCP failed for {module.xml_barcode} (attempt {attempt}/{retries}): {last_error}")
            if attempt < retries:
                print(f"Retrying SCP for {module.xml_barcode} in 3 seconds...\n")
                time.sleep(3)
        except Exception as exc:  # pragma: no cover - defensive only
            last_error = str(exc)
            print(f"SCP exception for {module.xml_barcode} (attempt {attempt}/{retries}): {last_error}")
            if attempt < retries:
                print(f"Retrying SCP for {module.xml_barcode} in 3 seconds...\n")
                time.sleep(3)
                continue
            raise RuntimeError(f"SCP upload failed for {module.xml_barcode}: {last_error}") from exc
    else:
        raise RuntimeError(f"SCP upload failed for {module.xml_barcode}: {last_error}")

    xml_filename = pathlib.Path(module.xml_path).name
    log_path = f"/home/dbspool/logs/mtd/{remote_db}/{xml_filename}"
    local_log_dir = pathlib.Path(outdir) / "xml_logs"
    local_log_dir.mkdir(parents=True, exist_ok=True)
    local_log_path = local_log_dir / f"{xml_filename}.log"
    cat_command = [
        "ssh",
        "-S",
        os.path.join(os.path.expanduser("~"), ".ssh", "socket_dbloader-mtd"),
        "mtd@dbloader-mtd.cern.ch",
        "cat",
        log_path,
    ]
    tail_command = ["tail", "-n", "1", str(local_log_path)]

    last_log_error = ""
    if retries > 0:
        time.sleep(2)
    for attempt in range(1, retries + 1):
        print(f"Log check attempt {attempt}/{retries} for {module.xml_barcode}")
        try:
            with local_log_path.open("w", encoding="utf-8") as local_log:
                cat_result = subprocess.run(
                    cat_command,
                    stdout=local_log,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
            if cat_result.returncode == 0:
                result = subprocess.run(
                    tail_command,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                last_log_error = (
                    cat_result.stderr.strip()
                    or f"cat exited with code {cat_result.returncode}"
                )
                if debug:
                    print_process_output("cat stderr", cat_result.stderr)
                print(
                    f"Upload log not ready for {module.xml_barcode} (attempt {attempt}/{retries}):"
                )
                print(f"{last_log_error}")
                if attempt < retries:
                    print(f"Retrying log check for {module.xml_barcode} in 3 seconds...\n")
                    time.sleep(3)
                continue
        except Exception as exc:  # pragma: no cover - defensive only
            last_log_error = str(exc)
            print(f"Upload log check exception for {module.xml_barcode} (attempt {attempt}/{retries}):")
            print(f"  {last_log_error}")
            if attempt < retries:
                print(f"Retrying log check for {module.xml_barcode} in 3 seconds...\n")
                time.sleep(3)
                continue
            raise RuntimeError(
                f"Upload log check failed for {module.xml_barcode}: {last_log_error}"
            ) from exc

        if result.returncode == 0:
            stdout_line = (result.stdout or "").strip()
            if debug:
                print_process_output("tail stdout", result.stdout)
                print_process_output("tail stderr", result.stderr)
            if "commit transaction" in stdout_line.lower():
                print(f"Upload log confirms commit transaction for {module.xml_barcode}")
                return
            raise RuntimeError(
                f"Upload for {module.xml_barcode} succeeded but did not contain a commit marker"
            )

        last_log_error = result.stderr.strip() or result.stdout.strip() or f"tail exited with code {result.returncode}"
        if debug:
            print_process_output("tail stdout", result.stdout)
            print_process_output("tail stderr", result.stderr)
        #print(f"Upload log not ready for {module.xml_barcode} (attempt {attempt}/{retries}):")
        #print(f"{last_log_error}")
        if attempt < retries:
            print(f"Retrying log check for {module.xml_barcode} in 3 seconds...\n")
            time.sleep(3)

    raise RuntimeError(
        f"Upload log check failed for {module.xml_barcode}: {last_log_error}"
    )


def write_upload_summary(
    successful_modules: list[str],
    failed_modules: list[str],
    outdir: str,
    total_modules: int,
    database: str,
) -> None:
    out_path = pathlib.Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    success_file = out_path / "modules_upload-successful.txt"
    failure_file = out_path / "modules_upload-failed.txt"
    success_file.write_text("\n".join(successful_modules) + ("\n" if successful_modules else ""), encoding="utf-8")
    failure_file.write_text("\n".join(failed_modules) + ("\n" if failed_modules else ""), encoding="utf-8")
    
    print("")
    print("="*80)
    print(f"Using database: {database}")
    print(f"{total_modules} module xmls found")
    print("")
    attempted = len(successful_modules) + len(failed_modules)
    print(f"Upload attempted for {attempted}/{total_modules} modules:")
    print(f"  {len(successful_modules)}/{attempted} successful, {len(failed_modules)}/{attempted} failed")
    print(f"  Successful modules written to: {success_file}")
    print(f"  Failed modules written to: {failure_file}")
    xml_logs_dir = out_path / "xml_logs"
    print(f"  Upload logs written to: {xml_logs_dir}")


def perform_uploads(
    modules: list[ModuleInfo],
    database: str,
    retries: int,
    outdir: str,
    debug: bool = False,
    total_modules: int = 0,
) -> tuple[list[str], list[str]]:
    successful_modules: list[str] = []
    failed_modules: list[str] = []

    for module in sorted(modules, key=lambda item: natural_sort_key(item.xml_barcode)):
        
        print("\n" + "="*80)
        print(f"Uploading module {module.xml_barcode} (version {module.xml_version}) to {database} ...")
        try:
            run_scp_upload(
                module,
                database=database,
                retries=retries,
                outdir=outdir,
                debug=debug,
            )
            successful_modules.append(module.xml_barcode)
            print(f"SUCCESS: {module.xml_barcode}")
        except RuntimeError as exc:
            failed_modules.append(module.xml_barcode)
            print(f"FAILED: {module.xml_barcode}: {exc}")

    write_upload_summary(successful_modules=successful_modules, failed_modules=failed_modules, outdir=outdir, total_modules=total_modules, database=database)
    return successful_modules, failed_modules


def summarize_updates(modules: list[ModuleInfo], database: str, verbose: bool = True) -> tuple[list[str], list[str]]:
    total_modules = len(modules)
    update_groups: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    missing_in_db: list[ModuleInfo] = []
    version_conflicts: list[ModuleInfo] = []
    lower_than_latest: list[ModuleInfo] = []

    for module in modules:
        if module.db_barcode is None:
            missing_in_db.append(module)
            continue
        if module.version_conflict:
            version_conflicts.append(module)
        if module.xml_version_lt_latest:
            lower_than_latest.append(module)
        if module.version_conflict or module.xml_version_lt_latest:
            continue
        update_groups[(module.db_latest_version, module.xml_version)].append(module.xml_barcode)

    if verbose:
        print(f"Using database: {database}")
        print(f"{total_modules} module xmls found")

    conflict_barcodes = natural_sort([module.xml_barcode for module in version_conflicts])
    if verbose:
        print(
            f"{len(version_conflicts)}/{total_modules} modules have a version conflict "
            "(XML version already exists in DB)"
        )
        if version_conflicts:
            for module in sorted(
                version_conflicts,
                key=lambda item: natural_sort_key(item.xml_barcode),
            ):
                db_version = module.db_latest_version if module.db_latest_version is not None else "null"
                print(f"  {module.xml_barcode} [XML version {module.xml_version}, DB version {db_version}]")

    lower_barcodes = natural_sort([module.xml_barcode for module in lower_than_latest])
    if verbose:
        print(
            f"{len(lower_than_latest)}/{total_modules} modules have XML version lower than latest DB version "
        )
        if lower_than_latest:
            for module in sorted(
                lower_than_latest,
                key=lambda item: natural_sort_key(item.xml_barcode),
            ):
                db_version = module.db_latest_version if module.db_latest_version is not None else "null"
                print(f"  {module.xml_barcode} [XML version {module.xml_version}, DB version {db_version}]")

    if verbose:
        if missing_in_db:
            missing_groups: dict[str, list[str]] = collections.defaultdict(list)
            for module in missing_in_db:
                missing_groups[module.xml_version].append(module.xml_barcode)

            for xml_version in natural_sort(list(missing_groups.keys())):
                module_barcodes = natural_sort(missing_groups[xml_version])
                count = len(module_barcodes)
                print(
                    f"{count}/{total_modules} modules not found on the database and will be updated to version {xml_version}"
                )
                for barcode in module_barcodes:
                    print(f"  {barcode}")
        else:
            print(f"0/{total_modules} modules not found on the database")

    return conflict_barcodes, lower_barcodes


def main() -> None:
    args = parse_args()

    xml_files = find_xml_files(args.srcs)

    modules: list[ModuleInfo] = []
    for xml_file in xml_files:
        match = FILENAME_REGEX.match(xml_file.name)
        if match is None:
            continue

        xml_barcode = match.group("barcode")
        xml_version = read_xml_version(xml_file)
        modules.append(
            ModuleInfo(
                xml_path=str(xml_file),
                xml_barcode=xml_barcode,
                xml_version=xml_version,
            )
        )

    if args.modules:
        allowed_modules = expand_module_filters(args.modules)
        modules = [module for module in modules if module.xml_barcode in allowed_modules]

    if args.skipmodules:
        skipped_modules = expand_module_filters(args.skipmodules)
        modules = [module for module in modules if module.xml_barcode not in skipped_modules]

    sorted_barcodes = natural_sort([module.xml_barcode for module in modules])
    barcode_order = {barcode: idx for idx, barcode in enumerate(sorted_barcodes)}
    modules = sorted(modules, key=lambda module: barcode_order[module.xml_barcode])

    module_barcodes = [module.xml_barcode for module in modules]
    versions_by_barcode = query_module_versions_bulk(
        barcodes=module_barcodes,
        database=args.database,
        port=args.port,
    )

    for module in modules:
        db_versions = versions_by_barcode[module.xml_barcode]
        module.db_barcode = module.xml_barcode if db_versions else None
        module.db_versions = db_versions
        module.db_latest_version = db_versions[-1] if db_versions else None
        module.version_conflict = module.xml_version in db_versions
        module.xml_version_lt_latest = (
            module.db_latest_version is not None and
            compare_natural_values(module.xml_version, module.db_latest_version) < 0
        )

    if args.verbose:
        for module in modules:
            print(
                f"module={module.xml_barcode}, "
                f"xml_version={module.xml_version}, "
                f"db_barcode={module.db_barcode if module.db_barcode is not None else 'null'}, "
                f"db_versions={module.db_versions}, "
                f"db_latest_version={module.db_latest_version if module.db_latest_version is not None else 'null'}, "
                f"version_conflict={module.version_conflict}, "
                f"xml_version_lt_latest={module.xml_version_lt_latest}, "
                f"file={module.xml_path}"
            )

    summarize_updates(modules=modules, database=args.database, verbose=True)
    total_modules = len(modules)

    if args.upload:
        upload_modules = select_modules_for_upload(modules)
        perform_uploads(
            modules=upload_modules,
            database=args.database,
            retries=args.retry,
            outdir=args.outdir,
            debug=args.debug,
            total_modules=total_modules,
        )

    conflict_barcodes, lower_barcodes = summarize_updates(modules=modules, database=args.database, verbose=False)
    out_path = pathlib.Path(args.outdir)
    out_path.mkdir(parents=True, exist_ok=True)
    conflict_file = out_path / "modules_version-conflict.txt"
    lower_version_file = out_path / "modules_bad-version.txt"
    conflict_file.write_text(
        "\n".join(conflict_barcodes) + ("\n" if conflict_barcodes else ""),
        encoding="utf-8",
    )
    lower_version_file.write_text(
        "\n".join(lower_barcodes) + ("\n" if lower_barcodes else ""),
        encoding="utf-8",
    )
    print("")
    print("="*80)
    version_problems = len(conflict_barcodes) + len(lower_barcodes)
    print(f"Version problems with {version_problems}/{total_modules} modules (no upload attempted):")
    print(f"  {len(conflict_barcodes)}/{version_problems} conflicts, {len(lower_barcodes)}/{version_problems} invalid versions")
    print(f"  Conflicts written to: {conflict_file}")
    print(f"  Invalid versions written to: {lower_version_file}")


if __name__ == "__main__":
    main()