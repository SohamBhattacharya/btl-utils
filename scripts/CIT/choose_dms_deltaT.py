#! /usr/bin/env python3

import ast
import numpy
import random
import subprocess

import python.utils as utils
from utils import logging
from utils import yaml

def main():
    
    dm_cat_file = "results/CIT/dm_summary/w-offset/DetectorModule_categorization.yaml"
    d_dm_info = None
    
    with open(dm_cat_file, "r") as fopen :
            
        d_dm_info = yaml.load(fopen.read())
    
    dbquery_output = subprocess.run([
        "./python/rhapi.py",
        "-u", "http://localhost:8113",
        "-a",
        "-f", "json2",
        "select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'DetectorModule' and (s.PART_PARENT_ID is NULL or s.PART_PARENT_ID = 1000) and s.LOCATION_ID = 5023",
    ], stdout = subprocess.PIPE, check = True)
    
    dbquery_output = dbquery_output.stdout.decode("utf-8")
    l_dms_tmp = ast.literal_eval(dbquery_output)["data"]
    l_dms_tmp = [str(_dm["barcode"]) for _dm in l_dms_tmp]
    
    l_bin_edges = [
        -21.0,
        -19.5,
        -19.0,
        -18.5,
        -18.0,
        -17.5,
        -17.0,
    ]
    
    nbins = len(l_bin_edges) - 1
    
    l_bin_nselect = [
        2,
        4,
        4,
        4,
        3,
        3,
    ]
    
    l_dms = []
    l_deltaT = []
    
    for dm in l_dms_tmp :
        
        #print(dm)
        
        if dm not in d_dm_info["results"] :
            continue
        
        dm_fname = d_dm_info["results"][dm]["fname"]
        
        parsed_result = utils.parse_string_regex(
            s = dm_fname,
            regexp = "run-(?P<run>\\d+)_DM-(?P<barcode>\\d+).root",
        )
        
        run = int(parsed_result["run"])
        #print(run)
        
        if run < 493 :
            continue
        
        deltaT = d_dm_info["results"][dm]["deltaT_avg"]
        
        if deltaT < l_bin_edges[0] or deltaT >= l_bin_edges[-1] :
            continue
        
        l_dms.append(dm)
        l_deltaT.append(d_dm_info["results"][dm]["deltaT_avg"])
    
    a_dms = numpy.array(l_dms, dtype = str)
    a_deltaT = numpy.array(l_deltaT)
    
    a_bin_idx = numpy.digitize(
        x = a_deltaT,
        bins = l_bin_edges
    )
    
    #print(a_bin_idx)
    
    rnd = random.Random(0)
    
    l_dms_selected = []
    l_deltaT_selected = []
    
    for bin_idx in range(1, nbins+1) :
        
        a_idx_inbin = numpy.argwhere(a_bin_idx == bin_idx)
        a_dms_inbin = a_dms[a_idx_inbin]
        a_deltaT_inbin = a_deltaT[a_idx_inbin]
        
        #print(a_dms_inbin)
        nselect = min(l_bin_nselect[bin_idx-1], len(a_dms_inbin))
        a_idx_selected = rnd.sample(list(range(0, len(a_dms_inbin))), k = nselect)
        a_dms_selected = a_dms_inbin[a_idx_selected].flatten()
        a_deltaT_selected = a_deltaT_inbin[a_idx_selected].flatten()
        
        l_dms_selected.extend(a_dms_selected)
        l_deltaT_selected.extend(a_deltaT_selected)
        #print(bin_idx, a_dms_selected, a_deltaT_selected)
        
        print(f"Selected {nselect} DMs with ΔT in range [{l_bin_edges[bin_idx-1]}, {l_bin_edges[bin_idx]}) C:")
        for idm in range(0, nselect) :
            
            print(f"  {a_dms_selected[idm]}: {a_deltaT_selected[idm]:0.2f} C")
    
    deltaT_mean = numpy.mean(l_deltaT_selected)
    deltaT_std = numpy.std(l_deltaT_selected)
    
    print(f"Selected total {len(l_deltaT_selected)} DMs with μ(ΔT) = {deltaT_mean:0.2f} C, σ(ΔT) = {deltaT_std:0.2f} C")
    print()
    
    return 0

if __name__ == "__main__":
    main()
