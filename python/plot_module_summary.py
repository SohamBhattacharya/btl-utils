#!/usr/bin/env python3

import argparse
import dataclasses
import glob
import itertools
import numpy
import os
import re
import ROOT
import sortedcontainers
import sys
import tqdm

from ruamel.yaml.scalarstring import DoubleQuotedScalarString

import constants
import utils
from utils import yaml


@dataclasses.dataclass(init = True)
class SensorModule(utils.SensorModule) :
    
    run: int = None
    fname: str = None
    category: str = None

@dataclasses.dataclass(init = True)
class DetectorModule(utils.DetectorModule) :
    
    run: int = None
    fname: str = None
    category: str = None

def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots module summary",
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
            "Keyed regular expression to extract run and barcode from the file name.\n   "
            "module example: \"run(?P<run>\\d+)/module_(?P<barcode>\\d+)_analysis_both_calibs.root\"\n   "
            "DM example: \"run-(?P<run>\\d+)_DM-(?P<barcode>\\d+).root\""
            "\n   "
        ),
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--plotcfg",
        help = "YAML file with plot configurations.\n   ",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--moduletype",
        help = "Module type.\n   ",
        type = str,
        required = True,
        choices = [constants.SM.KIND_OF_PART, constants.DM.KIND_OF_PART]
    )
    
    parser.add_argument(
        "--skipmodules",
        help = "List of SM barcodes (or files with a barcode per line) to skip.\n   ",
        type = str,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--skipruns",
        help = "List of runs to skip.\n   ",
        type = int,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--sipminfo",
        help = "YAML file with SiPM information.\n   ",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--sminfo",
        help = "YAML file with module information.\n   ",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--dminfo",
        help = "YAML file with DM information.\n   ",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--catcfg",
        help = "YAML file with module categorization configuration.\n   ",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--outdir",
        help = "Output directory.\n   ",
        type = str,
        required = True,
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get the list of files with specified pattern
    print(f"Getting list of files from {len(args.srcs)} source(s) ...")
    l_fnames = utils.get_file_list(l_srcs = args.srcs, regexp = args.regexp)
    
    d_loaded_part_info = {
        constants.SIPM.KIND_OF_PART: {},
        constants.SM.KIND_OF_PART: {},
        constants.DM.KIND_OF_PART: {},
    }
    
    if (args.sipminfo) :
        
        print("Loading SiPM information from {args.sipminfo} ...")
        d_loaded_part_info[constants.SIPM.KIND_OF_PART] = utils.load_part_info(parttype = constants.SIPM.KIND_OF_PART, yamlfile = args.sipminfo)
        print(f"Loaded information for {len(d_loaded_part_info[constants.SIPM.KIND_OF_PART])} SiPMs.")
    
    if (args.sminfo) :
        
        print("Loading SM information from {args.sminfo} ...")
        d_loaded_part_info[constants.SM.KIND_OF_PART] = utils.load_part_info(parttype = constants.SM.KIND_OF_PART, yamlfile = args.sminfo)
        print(f"Loaded information for {len(d_loaded_part_info[constants.SM.KIND_OF_PART])} SMs.")
    
    if (args.dminfo) :
        
        print("Loading DM information from {args.dminfo} ...")
        d_loaded_part_info[constants.DM.KIND_OF_PART] = utils.load_part_info(parttype = constants.DM.KIND_OF_PART, yamlfile = args.dminfo)
        print(f"Loaded information for {len(d_loaded_part_info[constants.DM.KIND_OF_PART])} DMs.")
    
    print("Combining parts ...")
    utils.combine_parts(
        d_sipms = d_loaded_part_info[constants.SIPM.KIND_OF_PART],
        d_sms = d_loaded_part_info[constants.SM.KIND_OF_PART],
        d_dms = d_loaded_part_info[constants.DM.KIND_OF_PART],
    )
    print("Combined parts.")
    
    # Get list of modules
    print(f"Parsing {len(l_fnames)} files to get modules to process ...")
    
    l_toskip_modules = []
    l_skipped_modules = []
    l_duplicate_modules = []
    d_modules = sortedcontainers.SortedDict()
    
    for toskip in args.skipmodules :
        
        if (os.path.isfile(toskip)) :
            
            l_tmp = numpy.loadtxt(toskip, dtype = str).flatten()
            l_toskip_modules.extend(l_tmp)
        
        else :
            
            l_toskip_modules.append(toskip)
    
    for fname in tqdm.tqdm(l_fnames) :
        
        parsed_result = utils.parse_string_regex(
            s = fname,
            regexp = args.regexp,
        )
        
        run = int(parsed_result["run"]) if ("run" in parsed_result) else -1
        barcode = parsed_result["barcode"].strip()
        
        if (run in args.skipruns or barcode in l_toskip_modules) :
            
            #print(f"Skipping module {barcode}")
            l_skipped_modules.append(barcode)
            continue
        
        # If the module is repeated, only use the latest run
        if (barcode in d_modules) :
            
            if (run < d_modules[barcode].run) :
                
                l_duplicate_modules.append({"run": run, "barcode": barcode, "fname": fname})
                continue
            
            else :
                
                l_duplicate_modules.append({"run": d_modules[barcode].run, "barcode": barcode, "fname": d_modules[barcode].fname})
        
        if (args.moduletype == constants.SM.KIND_OF_PART) :
            
            d_modules[barcode] = SensorModule(
                barcode = barcode,
                lyso = d_loaded_part_info[constants.SM.KIND_OF_PART][barcode].lyso if barcode in d_loaded_part_info[constants.SM.KIND_OF_PART] else "0",
                sipm1 = d_loaded_part_info[constants.SM.KIND_OF_PART][barcode].sipm1 if barcode in d_loaded_part_info[constants.SM.KIND_OF_PART] else "0",
                sipm2 = d_loaded_part_info[constants.SM.KIND_OF_PART][barcode].sipm2 if barcode in d_loaded_part_info[constants.SM.KIND_OF_PART] else "0",
                run = run,
                fname = fname
            )
        
        elif (args.moduletype == constants.DM.KIND_OF_PART) :
            
            d_modules[barcode] = DetectorModule(
                barcode = barcode,
                sm1 = d_loaded_part_info[constants.DM.KIND_OF_PART][barcode].sm1 if barcode in d_loaded_part_info[constants.DM.KIND_OF_PART] else "0",
                sm2 = d_loaded_part_info[constants.DM.KIND_OF_PART][barcode].sm2 if barcode in d_loaded_part_info[constants.DM.KIND_OF_PART] else "0",
                run = run,
                fname = fname
            )
    
    print(f"Skipped {len(l_skipped_modules)} modules:")
    print("\n".join(l_skipped_modules))
    print()
    
    print(f"Skipped {len(l_duplicate_modules)} duplicate modules:")
    print("#Run Barcode Filename")
    for module in l_duplicate_modules :
        
        print(f"{module['run']} {module['barcode']} {module['fname']}")
    
    print()
    
    # Read the plot config yaml
    d_plotcfgs = None
    
    with open(args.plotcfg, "r") as fopen :
        
        d_plotcfgs = yaml.load(fopen.read())
    
    # Read the category config yaml
    d_catcfgs = None
    
    with open(args.catcfg, "r") as fopen :
        
        d_catcfgs = yaml.load(fopen.read())
    
    d_cat_results = {
        "categories": d_catcfgs["categories"],
        "counts": {_key: 0 for _key in d_catcfgs["categories"].keys()},
        "modules": {_key: [] for _key in d_catcfgs["categories"].keys()},
        "results": {}
    }
    
    # Process the files
    print(f"Processing {len(d_modules)} modules ...")
    
    d_ones = {}
    
    for module in tqdm.tqdm(d_modules.values()) :
        
        rootfile = ROOT.TFile.Open(module.fname)
        
        d_module_cat = utils.eval_category(
            rootfile = rootfile,
            d_catcfgs = d_catcfgs,
            barcode = module.barcode
        )
        
        module.category = d_module_cat["category"]
        d_cat_results["counts"][module.category] += 1
        d_cat_results["modules"][module.category].append(DoubleQuotedScalarString(module.barcode))
        d_cat_results["results"][module.barcode] = {
            "category": DoubleQuotedScalarString(module.category),
            **d_module_cat["metrics"],
            "fname": DoubleQuotedScalarString(module.fname),
        }
        
        for plotname, plotcfg in d_plotcfgs.items() :
            
            for entryname, entrycfg in plotcfg["entries"].items() :
                
                plot_arr = None
                nelements = None
                
                d_fmt = {**module.dict()}
                
                d_read_info = {}
                
                for varkey, varname in entrycfg.get("read", {}).items() :
                    
                    d_read_info[varkey] = rootfile.Get(varname)
                    d_fmt[varkey] = f"d_read_info['{varkey}']"
                
                if (plotcfg["type"] == "hist1") :
                    
                    if "hist" not in entrycfg :
                        
                        hist_tmp = ROOT.TH1F(
                            entryname,
                            entrycfg["label"],
                            plotcfg["nbins"],
                            plotcfg["xmin"],
                            plotcfg["xmax"],
                        )
                        
                        hist_tmp.SetDirectory(0)
                        hist_tmp.SetOption("hist")
                        hist_tmp.SetLineWidth(2)
                        hist_tmp.SetLineColor(entrycfg["color"])
                        hist_tmp.SetFillColor(entrycfg["color"])
                        hist_tmp.SetFillStyle(entrycfg["fillstyle"])
                        
                        #entrycfg["hist"] = hist_tmp
                        d_plotcfgs[plotname]["entries"][entryname]["hist"] = hist_tmp
                    
                    plot_str = entrycfg["plot"].format(**d_fmt)
                    plot_arr = numpy.array(eval(plot_str)).flatten()
                    
                    nelements = len(plot_arr)
                    
                    # Create and store arrays of ones of specific lengths; no need to recreate them everytime
                    if nelements not in d_ones :
                        
                        d_ones[nelements] = numpy.ones(nelements)
                    
                    entrycfg["hist"].FillN(
                        nelements,
                        plot_arr,
                        d_ones[nelements]
                    )
                
                elif (plotcfg["type"] == "graph") :
                    
                    if ("graph" not in entrycfg) :
                        
                        gr_tmp = ROOT.TGraph()
                        gr_tmp.SetName(entryname)
                        gr_tmp.SetTitle(entrycfg["label"])
                        
                        gr_tmp.SetLineWidth(2)
                        gr_tmp.SetLineColor(entrycfg["color"])
                        gr_tmp.SetMarkerColor(entrycfg["color"])
                        gr_tmp.SetMarkerSize(entrycfg["size"])
                        gr_tmp.SetMarkerStyle(entrycfg["marker"])
                        gr_tmp.SetFillStyle(0)
                        
                        d_plotcfgs[plotname]["entries"][entryname]["graph"] = gr_tmp
                    
                    plotx_str = entrycfg["plotx"].format(**d_fmt)
                    ploty_str = entrycfg["ploty"].format(**d_fmt)
                    
                    plotx_arr = numpy.array(eval(plotx_str)).flatten()
                    ploty_arr = numpy.array(eval(ploty_str)).flatten()
                    
                    if (len(plotx_arr) != len(ploty_arr)) :
                        
                        print(f"Error: Mismatch in x and y data dimensions for plot \"{plotname}\".")
                        print(f"  x[{len(plotx_arr)}]: {plotx_arr}")
                        print(f"  y[{len(ploty_arr)}]: {ploty_arr}")
                        sys.exit(1)
                    
                    for plotx, ploty in numpy.dstack((plotx_arr, ploty_arr))[0] :
                        
                        # Fix the outliers to the outer range
                        ploty = max(plotcfg["ymin"], ploty)
                        ploty = min(plotcfg["ymax"], ploty)
                        
                        entrycfg["graph"].AddPoint(plotx, ploty)
                
                else :
                    
                    print(f"Error: Invalid plot type \"{plotcfg['type']}\" for plot \"{plotname}\".")
                    sys.exit(1)
        
        rootfile.Close()
    
    for plotname, plotcfg in d_plotcfgs.items() :
        
        if (plotcfg["type"] == "hist1") :
            
            l_hists = [_entrycfg["hist"] for _entrycfg in plotcfg["entries"].values()]
            
            for hist in l_hists :
                
                utils.handle_flows(hist)
                
                mean = hist.GetMean()
                mean_str = f"{round(mean)}" if mean > 100 else f"{mean:0.2f}"
                stddev = hist.GetStdDev()
                
                hist.SetTitle(f"{hist.GetTitle()} [#mu: {mean_str}, #sigma/#mu: {stddev/abs(mean)*100:0.2f}%]")
            
            utils.root_plot1D(
                l_hist = l_hists,
                outfile = f"{args.outdir}/{plotname}.pdf",
                xrange = (plotcfg["xmin"], plotcfg["xmax"]),
                yrange = (0.5, 10 * max([_hist.GetMaximum() for _hist in l_hists])),
                logx = plotcfg.get("logx", False),
                logy = plotcfg.get("logy", True),
                xtitle = plotcfg["xtitle"],
                ytitle = plotcfg["ytitle"],
                gridx = plotcfg.get("gridx", True),
                gridy = plotcfg.get("gridy", True),
                ndivisionsx = None,
                ndivisionsy = None,
                stackdrawopt = "nostack",
                legendpos = "UR",
                legendncol = 1,
                legendfillstyle = 0,
                legendfillcolor = 0,
                legendtextsize = 0.045,
                legendtitle = "",
                legendheightscale = 1.0,
                legendwidthscale = 2.0,
                CMSextraText = "BTL Internal",
                lumiText = "Phase-2"
            )
        
        
        elif (plotcfg["type"] == "graph") :
            
            l_graphs = []
            
            for entrycfg in plotcfg["entries"].values() :
                
                gr = entrycfg["graph"]
                
                #for fnname, fnstr in entrycfg.get("fit", {}).items() :
                #    
                #    f1 = ROOT.TF1(fnname, fnstr, plotcfg["xmin"], plotcfg["xmax"])
                #    f1.SetLineWidth(2)
                #    f1.SetLineStyle(7)
                #    f1.SetLineColor(entrycfg["color"])
                #    
                #    fit_res = gr.Fit(
                #        f1,
                #        option = "SEM",
                #        goption = "L",
                #        xmin = plotcfg["xmin"],
                #        xmax = plotcfg["xmax"]
                #    )
                #    
                #    #print("Fitted")
                
                gr.GetHistogram().SetOption(entrycfg["drawopt"])
                l_graphs.append(gr)
            
            utils.root_plot1D(
                l_hist = [ROOT.TH1F(f"h1_tmp_{plotname}", "", 1, plotcfg["xmin"], plotcfg["xmax"])],
                outfile = f"{args.outdir}/{plotname}.pdf",
                xrange = (plotcfg["xmin"], plotcfg["xmax"]),
                yrange = (plotcfg["ymin"], plotcfg["ymax"]),
                l_graph_overlay = l_graphs,
                logx = plotcfg.get("logx", False),
                logy = plotcfg.get("logy", False),
                xtitle = plotcfg["xtitle"],
                ytitle = plotcfg["ytitle"],
                gridx = plotcfg.get("gridx", True),
                gridy = plotcfg.get("gridy", True),
                ndivisionsx = None,
                ndivisionsy = None,
                stackdrawopt = "nostack",
                legendpos = "UR",
                legendncol = 1,
                legendfillstyle = 0,
                legendfillcolor = 0,
                legendtextsize = 0.045,
                legendtitle = "",
                legendheightscale = 1.0,
                legendwidthscale = 2.0,
                CMSextraText = "BTL Internal",
                lumiText = "Phase-2"
            )
    
    #l_files_to_copy = [
    #    args.plotcfg,
    #    args.sminfo,
    #    args.catcfg,
    #]
    
    # Save the categorization
    outfname = f"{args.outdir}/module_categorization.yaml"
    print(f"Writing categorizations to file ...")
    
    with open(outfname, "w") as fopen:
        
        yaml.dump(d_cat_results, fopen)
    
    print(f"Written categorizations to file: {outfname}")



if __name__ == "__main__" :
    
    main()