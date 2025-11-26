#!/usr/bin/env python3

import argparse
import dataclasses
import glob
import importlib
import itertools
import numpy
import os
import random
import re
import ROOT
import sortedcontainers
import sys
import tqdm

import constants
import utils
from utils import logging
from utils import yaml

def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots module summary",
    )
    
    parser.add_argument(
        "--dmresults",
        help = (
            "YAML file with the DM results, for example the DM categorization output file."
        ),
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--dms",
        help = "Space delimited list of DMs (or files with a barcode per line) to replace.\n",
        type = str,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--location",
        help = "List of locations \n",
        type = str,
        nargs = "+",
        required = True,
        choices = [_loc for _loc in dir(constants.LOCATION) if not _loc.startswith("__")],
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    l_loc_ids = [getattr(constants.LOCATION, _loc) for _loc in args.location]
    
    l_dms_to_replace = []
    for dm in args.dms :
        
        if (os.path.isfile(dm)) :
            
            l_tmp = numpy.loadtxt(dm, dtype = str).flatten()
            l_dms_to_replace.extend(l_tmp)
        
        else :
            
            l_dms_to_replace.append(dm)
    
    d_dm_results = {}
    logging.info(f"Loading results from file: {args.dmresults} ...")
    with open(args.dmresults, "r") as fopen :
        
        d_dm_results = yaml.load(fopen.read())["results"]
    
    l_dms_to_replace = utils.natural_sort(list(set(l_dms_to_replace)))
    #print(l_dms_to_replace)
    
    l_avalable_dms = utils.run_db_query(
        "select s.BARCODE from mtd_cmsr.parts s"
        f" where s.KIND_OF_PART = '{constants.DM.KIND_OF_PART}'"
        " and ((s.PART_PARENT_ID is NULL) or (s.PART_PARENT_ID = 1000))"
        f" and s.LOCATION_ID in {str(tuple(l_loc_ids)).replace(',)', ')')}"
    )
    
    l_avalable_dms = [_dm["barcode"] for _dm in l_avalable_dms]
    
    #print(l_avalable_dms)
    
    for dm1 in l_dms_to_replace :
        
        if dm1 not in d_dm_results :
            logging.warning(f"DM {dm1} not found in file {args.dmresults}")
            continue
        
        l_matched_dms = []
        
        for dm2 in l_avalable_dms :
            
            if (dm2 == dm1) or (dm2 in l_dms_to_replace) or (dm2 not in d_dm_results) :
                continue
            
            grouping_diff = abs(d_dm_results[dm1]["grouping"]/d_dm_results[dm2]["grouping"] - 1)
            
            match_cond = (
                d_dm_results[dm1]["category"] == d_dm_results[dm2]["category"]
                and d_dm_results[dm1]["nfoamlayers"] == d_dm_results[dm2]["nfoamlayers"]
                and grouping_diff < 0.1
            )
            
            if match_cond :
                l_matched_dms.append((dm2, grouping_diff))
        
        l_matched_dms = sorted(l_matched_dms, key = lambda _dm : _dm[1])
        
        print(
            f"Found {len(l_matched_dms)} DMs matched to {dm1}"
            f" [category: {d_dm_results[dm1]['category']}, nfoamlayers: {d_dm_results[dm1]['nfoamlayers']}, grouping: {d_dm_results[dm1]['grouping']:.2f}]."
            #f"[grouping: {d_dm_results[dm1]['grouping']}]."
        )
        
        if l_matched_dms :
            
            for dm2, grouping_diff in l_matched_dms :
                #print(f"  {dm2} [category: {d_dm_results[dm2]['category']}, nfoamlayers: {d_dm_results[dm2]['nfoamlayers']}, grouping: {d_dm_results[dm2]['grouping']}]")
                print(
                    f"  {dm2} ["
                    f"category: {d_dm_results[dm2]['category']}"
                    f", nfoamlayers: {d_dm_results[dm2]['nfoamlayers']}"
                    f", grouping: {d_dm_results[dm2]['grouping']:.2f} (Δ = {grouping_diff*100:.2f}%)" \
                    "]"
                )
    
    return 0


if __name__ == "__main__" :
    main()