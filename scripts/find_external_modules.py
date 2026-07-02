#!/usr/bin/env python3

import argparse
import tqdm

import python.constants as constants
import python.utils as utils


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Find QAQC runs for modules from external BACs",
    )
    
    parser.add_argument(
        "--srcs",
        help = (
            "Source directories and regular expressions for each source: dir1:regexp1 dir1:regexp2 ...\n"
            "Only files that match the regular expression will be processed.\n"
            "regexp is a keyed regular expression, used to extract run and barcode from the file name.\n"
            "SM example (for cases like \"runXXXX/module_YYYY_analysis.root\"): \"run(?P<run>\\d+)/module_(?P<barcode>\\d+)_analysis.root\"\n"
            "DM example (for cases like \"runXXXX_DM-YYYY.root\"): \"run-(?P<run>\\d+)_DM-(?P<barcode>\\d+).root\""
            "\n"
        ),
        type = str,
        nargs = "+",
        required = True,
    )
    
    parser.add_argument(
        "--moduletype",
        help = "Module type.\n",
        type = str,
        required = True,
        choices = [constants.SM.KIND_OF_PART, constants.DM.KIND_OF_PART]
    )
    
    parser.add_argument(
        "--location",
        help = "Location. \n",
        type = str,
        required = True,
        choices = [_loc for _loc in dir(constants.LOCATION) if not _loc.startswith("__")],
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    l_srcs = [_src.split(":")[0] for _src in args.srcs]
    l_regexps = [_src.split(":")[1] for _src in args.srcs]
    l_fnames, l_regexps = utils.get_file_list(l_srcs = l_srcs, l_regexps = l_regexps)
    
    location_id = getattr(constants.LOCATION, args.location)
    
    l_fnames_external = []
    
    for fname, regexp in tqdm.tqdm(zip(l_fnames, l_regexps)) :
        
        parsed_result = utils.parse_string_regex(
            s = fname,
            regexp = regexp,
        )
        
        run = int(parsed_result["run"]) if ("run" in parsed_result) else -1
        barcode = parsed_result["barcode"].strip()
        
        #barcode_ranges = getattr(constants, args.moduletype).BARCODE_RANGES[location_id]
        barcode_ranges = getattr(constants, "SM").BARCODE_RANGES[location_id]
        
        cond_str = " or ".join([
            f"({barcode} > {_range[0]} and {barcode} < {_range[1]})" for _range in barcode_ranges
        ])
        
        if eval(cond_str) :
            continue
        
        l_fnames_external.append(fname)
    
    print("\n".join(l_fnames_external))
    
    return 0


if __name__ == "__main__":
    main()