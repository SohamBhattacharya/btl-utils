#!/usr/bin/env python3

import argparse
import os
import python.constants as constants
import python.utils as utils
from utils import yaml
from utils import logging


def main() :
    
    l_locations = [_loc for _loc in dir(constants.LOCATION) if not _loc.startswith("__")]
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots module summary",
    )
    
    parser.add_argument(
        "--runsdir",
        help = "Path to the directory containing the runs",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--plotsdir",
        help = "Path to the directory containing the plots",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--dst",
        help = "Path to destination directory. Will create the directory structure tray/RU/run_type/run under this path.",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--gencfg",
        help = "YAML file containing the general configuration",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--traycfgs",
        help = "YAML files containing the tray configuration",
        type = str,
        required = True,
        nargs = "+",
    )
    
    parser.add_argument(
        "--nocopy",
        help = "Will not not copy anything; the tray/RU/run_type/run directory structure will not be created",
        action = "store_true",
        default = False,
    )
    
    parser.add_argument(
        "--nocompress",
        help = "Will not create a tar.xz file for each tray",
        action = "store_true",
        default = False,
    )
    
    parser.add_argument(
        "--eos",
        help = (
            "If provided, will transfer the tar.xz file to EOS and untar there.\n"
            "Syntax is: --eos <lxplus username> <location>\n"
            f"location is one of {l_locations}"
        ),
        type = str,
        nargs = 2,
        required = False,
        default = None,
    )
    
    args = parser.parse_args()
    
    lxplus_user = args.eos[0] if args.eos else None
    location = args.eos[1] if args.eos else None
    
    assert location in l_locations, f"Invalid location: {location}. Must be one of {l_locations}."
    
    d_cfg = {"trays": {}}
    
    logging.info(f"Loading configuration from: {args.gencfg}")
    d_gencfg = utils.load_yaml_file(args.gencfg)
    d_cfg.update(d_gencfg)
    
    for cfg in args.traycfgs:
        logging.info(f"Loading configuration from: {cfg}")
        d_traycfg = utils.load_yaml_file(cfg)
        d_cfg["trays"].update(d_traycfg)
    
    #print(d_gencfg)
    #print(d_traycfg)
    
    l_cmds = []
    
    for tray, d_tray_cfg in d_cfg["trays"].items():
        
        outdir_tray = f"{args.dst}/{tray}"
        #outdir_tray = f"/tmp/{tray}"
        #outdir_tray_tmp = f"/tmp/{tray}"
        
        if not args.nocopy:
            
            for ru, d_ru_cfg in d_tray_cfg.items():
                
                for run_type, d_run_cfg in d_ru_cfg.items() :
                    
                    outdir = f"{outdir_tray}/{ru}/{run_type}"
                    
                    cmd = f"mkdir -p {outdir}"
                    l_cmds.append(cmd)
                    
                    l_runs = d_run_cfg["runs"]
                    
                    for run in l_runs :
                        
                        d_fmt = {
                            "run": run,
                            "runstart": run,
                            "runend": run + 11,
                            "runsdir": args.runsdir,
                            "plotsdir": args.plotsdir,
                        }
                        
                        plotsdir = d_cfg["run_types"][run_type]["plotsdir"].format(**d_fmt)
                        #plotsdir_name = os.path.basename(plotsdir)
                        #print(plotsdir)
                        
                        l_excludes = d_cfg["run_types"][run_type].get("exclude", [])
                        
                        exclude_str = " ".join([f"--exclude \"{_exc}\"" for _exc in l_excludes])
                        
                        #cmd = f"cp -rvu {plotsdir} {outdir}/"
                        #cmd = f"rsync -asP -z --zc lz4 --prune-empty-dirs --inplace {exclude_str} {plotsdir} {outdir}/"
                        #cmd = f"rsync -asP --prune-empty-dirs --inplace {exclude_str} {plotsdir} {outdir}/"
                        cmd = f"./scripts/msrsync3 -p 8 -P --stats --rsync \'-as --prune-empty-dirs {exclude_str}\' {plotsdir} {outdir}/"
                        print(cmd)
                        
                        l_cmds.append(cmd)
        
        if not args.nocompress:
            
            cmd = f"cd `dirname {outdir_tray}` && tar -c -I 'zstd -22 -T0' -f {tray}.tar.xz {tray}"
            l_cmds.append(cmd)
        
        if args.eos:
            
            cmd = f"./scripts/transfer-results-eos_tray-qaqc.sh {outdir_tray}.tar.xz {lxplus_user} {location}"
            l_cmds.append(cmd)
    
    utils.run_cmd_list(l_cmds, debug = True)
    
    return 0

if __name__ == "__main__":
    main()