#!/usr/bin/env python3

import argparse
import dataclasses
import glob
import itertools
import numpy
import os
import re
import ROOT
import tqdm

import utils


@dataclasses.dataclass(init = True)
class SensorModule :
    
    barcode: str = None
    run: int = None
    file: str = None
    
    #bar_L_ly: list[float] = None
    #bar_R_ly: list[float] = None
    #bar_avg_ly: list[float] = None
    
    bar_L_ly: ROOT.TGraph = None
    bar_R_ly: ROOT.TGraph = None
    bar_avg_ly: ROOT.TGraph = None
    
    bar_L_peak_res: ROOT.TGraph = None
    bar_R_peak_res: ROOT.TGraph = None
    bar_avg_peak_res: ROOT.TGraph = None
    
    def bar_avg_ly_mean(self) :
        
        return self.bar_avg_ly.GetMean(axis = 2)
    
    def module_class(self) :
        
        max_res = 0.045
        min_ch_ly = 0.85 * 3200
        min_bar_ly = 0.9 * 3200
        
        module_class = 0
        
        #arr_bar_L_peak_res = numpy.array(self.bar_L_peak_res.GetY())
        #arr_bar_R_peak_res = numpy.array(self.bar_R_peak_res.GetY())
        
        arr_bar_avg_peak_res = numpy.array(self.bar_avg_peak_res.GetY())
        arr_bar_L_ly  = numpy.array(self.bar_L_ly.GetY())
        arr_bar_R_ly  = numpy.array(self.bar_R_ly.GetY())
        arr_bar_avg_ly = numpy.array(self.bar_R_ly.GetY())
        
        if (
            numpy.sum(arr_bar_avg_peak_res > max_res) or
            numpy.sum(arr_bar_L_ly < min_ch_ly) or
            numpy.sum(arr_bar_R_ly < min_ch_ly) or
            numpy.sum(arr_bar_avg_ly < min_bar_ly)
            ) :
            
            module_class = 1
        
        return module_class


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Pairs sensor modules with similar light yields for assembling detector modules",
        epilog = (
            "Needs to communicate with database; before running this script, open a tunnel with:\n"
            "ssh -f -N -L 8113:dbloader-mtd.cern.ch:8113 username@lxplus.cern.ch"
            "\n"
        ),
    )
    
    parser.add_argument(
        "--srcs",
        help = "Source directories.\n   ",
        type = str,
        nargs = "+",
        required = True,
    )
    
    parser.add_argument(
        "--regexp",
        help = (
            "Keyed regular expression to extract run and SM barcode from the file name.\n"
            "Generally the file path has the form run[RUN]/module_[BARCODE]_analysis.root"
            "\n   "
        ),
        type = str,
        required = False,
        default = "run(?P<run>\d+)/module_(?P<barcode>\d+)_analysis_both_calibs.root"
    )
    
    parser.add_argument(
        "--skip",
        help = "List of SM barcodes to skip.\n   ",
        type = int,
        nargs = "+",
        required = False,
    )
    
    parser.add_argument(
        "--dmyaml",
        help = (
            "Yaml file with DM information to load. Should be provided if it exists, as it is much faster than querying the database.\n"
            "If the provided filename does not exist, it will be created with the information fetched from the database.\n"
            "If the file exists, it will be updated with DM information from the database."
            "\n   "
        ),
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--location",
        help = "Location ID: 5023 for CIT, 5380 for MIB, 3800 for PKU, 1003 for UVA \n   ",
        type = int,
        required = False,
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    d_produced_dms = utils.save_all_dm_info(
        outyamlfile = args.dmyaml,
        inyamlfile = args.dmyaml,
        location_id = args.location,
        ret = True
    )
    
    l_all_used_sm_barcodes = list(itertools.chain(*[[_dm.sm1, _dm.sm2] for _dm in d_produced_dms.values()]))
    #print(l_all_used_sm_barcodes)
    
    l_fnames = []
    
    rgx = re.compile(args.regexp)
    
    d_sms = {}
    l_used_sm_barcodes = []
    l_skipped_sm_barcodes = []
    
    # Get the list of files with specified extensions
    print(f"Getting list of files from {len(args.srcs)} source(s) ...")
    
    for src in tqdm.tqdm(args.srcs) :
        
        while "//" in src:
            
            src = src.replace("//", "/")
        
        l_tmp = glob.glob(f"{src}/**", recursive = True)
        l_tmp = [_f for _f in l_tmp if os.path.isfile(_f) and rgx.search(_f)]
        l_fnames.extend(l_tmp)
    
    
    print(f"Reading SM information from {len(l_fnames)} file(s) ...")
    
    for fname in tqdm.tqdm(l_fnames) :
        
        parsed_result = utils.parse_string_regex(
            s = fname,
            regexp = args.regexp,
        )
        
        run = int(parsed_result["run"]) if ("run" in parsed_result) else -1
        barcode = parsed_result["barcode"].strip()
        
        rootfile = ROOT.TFile.Open(fname)
        
        #gr_bar_ly = rootfile.Get("g_avg_light_yield_vs_bar")
        #bar_avg_ly_mean = gr_bar_ly.GetMean(axis = 2)
        
        # If the SM ID is repeated, only use the latest run
        if (barcode in d_sms and run < d_sms[barcode].run) :
            
            continue
        
        if (args.skip and barcode in args.skip) :
            
            l_skipped_sm_barcodes.append(barcode)
            continue
        
        if (barcode in l_all_used_sm_barcodes) :
            
            l_used_sm_barcodes.append(barcode)
            continue
        
        sm_tmp = SensorModule(
            barcode = barcode,
            run = run,
            file = fname,
            
            bar_L_ly = rootfile.Get("g_L_light_yield_vs_bar"),
            bar_R_ly = rootfile.Get("g_R_light_yield_vs_bar"),
            bar_avg_ly = rootfile.Get("g_avg_light_yield_vs_bar"),
            
            bar_L_peak_res = rootfile.Get("g_lyso_L_peak_res_vs_bar"),
            bar_R_peak_res = rootfile.Get("g_lyso_R_peak_res_vs_bar"),
            bar_avg_peak_res = rootfile.Get("g_avg_lyso_res_vs_bar"),
        )
        
        if (sm_tmp.module_class() > 0) :
            
            l_skipped_sm_barcodes.append(barcode)
            continue
        
        d_sms[barcode] = sm_tmp
        
        #print(f"run: {run}, barcode: {barcode}, {bar_avg_ly_mean()}")
        
        rootfile.Close()
    
    l_sms_sorted = sorted(d_sms.values(), key = lambda _x: _x.bar_avg_ly_mean())
    n_sms = len(l_sms_sorted)
    
    print()
    print(f"Finding pairs in {n_sms} SMs ...")
    
    l_sm_group = [l_sms_sorted[_i: _i+2] if (_i < n_sms-1) else l_sms_sorted[_i: _i+1] for _i in range(0, n_sms, 2) ]
    
    l_paired_sms = []
    l_unpaired_sms = []
    
    for ipair, pair in enumerate(l_sm_group) :
        
        if (len(pair) != 2) :
            
            l_unpaired_sms.extend(pair)
            continue
        
        # Sort by barcode
        pair = sorted(pair, key = lambda _x: _x.barcode)
        
        l_paired_sms.append(pair)
    
    print()
    print(f"{len(l_paired_sms)} paired SMs. Barcodes:")
    for pair in l_paired_sms :
        
        print(f"{pair[0].barcode} , {pair[1].barcode}")
    
    print()
    print("Paired SM details:")
    for ipair, pair in enumerate(l_paired_sms) :
        
        sm1 = pair[0]
        sm2 = pair[1]
        
        ly_asym = 100 * abs(sm1.bar_avg_ly_mean()-sm2.bar_avg_ly_mean())/numpy.mean([sm1.bar_avg_ly_mean(), sm2.bar_avg_ly_mean()])
        
        print()
        print(f"Pair {ipair+1}:")
        print(f"    SM 1: Barcode = {sm1.barcode} , <Bar LY> = {sm1.bar_avg_ly_mean():0.2f}, Run = {sm1.run}")
        print(f"    SM 2: Barcode = {sm2.barcode} , <Bar LY> = {sm2.bar_avg_ly_mean():0.2f}, Run = {sm2.run}")
        print(f"    <bar LY> asymmetry = {ly_asym:0.2f} %")
    
    print()
    print(f"{len(l_unpaired_sms)} unpaired SMs:")
    for sm in l_unpaired_sms :
        
        print(f"Barcode = {sm.barcode} , <Bar LY> = {sm.bar_avg_ly_mean():0.2f} , Run = {sm.run}")
    
    print()
    print(f"{len(l_skipped_sm_barcodes)} skipped SMs (failed QA/QC criteria). Barcodes:")
    for barcode in l_skipped_sm_barcodes :
        
        print(f"{barcode}")
    
    print()
    print(f"{len(l_used_sm_barcodes)} skipped SMs (already used in DMs). Barcodes:")
    for barcode in l_used_sm_barcodes :
        
        print(f"{barcode}")


if __name__ == "__main__" :
    
    main()