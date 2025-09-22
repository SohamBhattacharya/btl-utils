#!/usr/bin/env python3

import argparse
import numpy
import os

import utils
from utils import logging
from utils import yaml


SIPM_BARCODE_BASE = 32110010000000


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "For each SiPM in list 1, finds a matching SiPM from list 2 based on the Vbr in the SiPM info file ",
    )
    
    parser.add_argument(
        "--sipminfo",
        help = "YAML file with SiPM information.\n",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--list1",
        help = "File with SiPM list 1 (one barcode per line).\n",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--list2",
        help = "File with SiPM list 2 (one barcode per line).\n",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--dsheet",
        help = "SiPM datasheet csv file; if provided, will show which tray each SiPM from list 2 is in.\n",
        type = str,
        required = False,
        default = None,
    )
    
    args = parser.parse_args()
    
    with open(args.sipminfo, "r") as fopen :
        
        d_sipminfo = yaml.load(fopen.read())
    
    def strip(s) :
        return s.strip()
    
    def sanitize(s) :
        return s.decode("utf-8").strip()
    
    l_sipms_1 = numpy.loadtxt(args.list1, dtype = str, converters = strip).flatten().tolist()
    l_sipms_2 = numpy.loadtxt(args.list2, dtype = str, converters = strip).flatten().tolist()
    
    l_sipms_1 = utils.natural_sort([_sipm if len(_sipm) == 14 else str(SIPM_BARCODE_BASE + int(_sipm)) for _sipm in l_sipms_1])
    l_sipms_2 = utils.natural_sort([_sipm if len(_sipm) == 14 else str(SIPM_BARCODE_BASE + int(_sipm)) for _sipm in l_sipms_2])
    
    #print("\n".join(l_sipms_1))
    
    l_sipms_1 = [_sipm for _sipm in l_sipms_1 if _sipm in d_sipminfo]
    l_sipms_2 = [_sipm for _sipm in l_sipms_2 if _sipm in d_sipminfo]
    
    #a_sipm_vbrs_1 = numpy.array([d_sipminfo[_sipm]["vbr_avg"] for _sipm in l_sipms_1 if _sipm in d_sipminfo])
    a_sipm_vbrs_2 = numpy.array([d_sipminfo[_sipm]["vbr_avg"] for _sipm in l_sipms_2 if _sipm in d_sipminfo])
    
    l_sipm_pairs = []
    
    a_dsheet = None
    d_sipm_tray = {}
    
    if args.dsheet :
        
        a_dsheet = numpy.loadtxt(args.dsheet, dtype = str, skiprows = 17, delimiter = ",", usecols = [0, 2], converters = sanitize)
        a_dsheet = a_dsheet[numpy.any(a_dsheet != ["", ""], axis = 1)]
        
        tray = ""
        
        for tray_tmp, sipm in a_dsheet :
            
            tray = tray_tmp if tray_tmp else tray
            d_sipm_tray[sipm] = tray
    
    #print(d_sipm_tray)
    
    for sipm in l_sipms_1 :
        
        vbr = d_sipminfo[sipm]["vbr_avg"]
        a_delta_vbr = numpy.abs(a_sipm_vbrs_2 - vbr)
        
        idx_min = numpy.argmin(a_delta_vbr)
        l_sipm_pairs.append((sipm, l_sipms_2[idx_min]))
        
        a_sipm_vbrs_2[idx_min] = 9999
    
    for sipm1, sipm2 in l_sipm_pairs :
        
        sipm1_short = f"{int(sipm1)-SIPM_BARCODE_BASE:05d}"
        sipm2_short = f"{int(sipm2)-SIPM_BARCODE_BASE:05d}"
        
        print(
            f"{sipm1_short} ({d_sipminfo[sipm1]['vbr_avg']:0.2f})"
            " , "
            f"{sipm2_short} ({d_sipminfo[sipm2]['vbr_avg']:0.2f}, {d_sipm_tray.get(sipm2_short, 'NA')})"
        )
    
    return 0


if __name__ == "__main__" :
    main()
