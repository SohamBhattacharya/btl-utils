#!/usr/bin/env python3

import argparse
import os
import python.utils as utils
from utils import logging


PHP_TEMPLATE = """
<?php
$protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
$host = $_SERVER['HTTP_HOST'];
$uri = $_SERVER['REQUEST_URI'];

$current_url = $protocol . '://' . $host . dirname($uri);
$target_url = $current_url . "/?match=RU*%2F{run_type}%2F*%2F{pattern}&depth={depth}";
?>
<!DOCTYPE html>
<head>
    <meta http-equiv="refresh" charset="utf-8" content="0; url=<?php echo $target_url; ?>" />
</head>
</html>
"""


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots module summary",
    )
    
    parser.add_argument(
        "--cfg",
        help = "YAML file containing the configuration",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--outdir",
        help = "Path to the output directory",
        type = str,
        required = True,
    )
    
    args = parser.parse_args()
    
    logging.info(f"Loading configuration from: {args.cfg}")
    d_cfg = utils.load_yaml_file(args.cfg)
    
    cmd = f"mkdir -p {args.outdir}"
    os.system(cmd)
    
    for run_type, link_cfgs in d_cfg.items() :
        
        for link_name, d_link_cfg in link_cfgs.items() :
            
            pattern = d_link_cfg["pattern"]
            depth = d_link_cfg["depth"]
            
            link_php = PHP_TEMPLATE.format(
                run_type = run_type,
                pattern = pattern,
                depth = depth,
            )
            
            link_fname = f"{args.outdir}/{run_type}__{link_name}.php"
            logging.info(f"Creating link file: {link_fname}")
            
            with open(link_fname, "w") as fopen:
                fopen.write(link_php)

    return 0

if __name__ == "__main__":
    main()