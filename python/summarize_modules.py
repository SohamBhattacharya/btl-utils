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
        help = "Source directories.\n",
        type = str,
        nargs = "+",
        required = True,
    )
    
    parser.add_argument(
        "--regexp",
        help = (
            "Keyed regular expression to extract run and barcode from the file name.\n"
            "SM example: \"run(?P<run>\\d+)/module_(?P<barcode>\\d+)_analysis_both_calibs.root\"\n"
            "DM example: \"run-(?P<run>\\d+)_DM-(?P<barcode>\\d+).root\""
            "\n"
        ),
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--plotcfg",
        help = "YAML file with plot configurations.\n",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--moduletype",
        help = "Module type.\n",
        type = str,
        required = True,
        choices = [constants.SM.KIND_OF_PART, constants.DM.KIND_OF_PART]
    )
    
    parser.add_argument(
        "--modules",
        help = "Only process this list of modules (or files with a barcode per line) to, unless it is in the skipmodules list.\n",
        type = str,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--skipmodules",
        help = "List of modules (or files with a barcode per line) to skip.\n",
        type = str,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--skipruns",
        help = "List of runs to skip.\n",
        type = int,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--sipminfo",
        help = "YAML file with SiPM information.\n",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--sminfo",
        help = "YAML file with module information.\n",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--dminfo",
        help = (
            "YAML file with DM information.\n"
            "Will update the file with additional DMs on the database, if --pairsms is passed.\n"
            "This is needed if one wants to omit the already used SMs from the pairing.\n"
        ),
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--catcfg",
        help = "YAML file with module categorization configuration.\n",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--pairsms",
        help = "Will pair SMs using the \"pairing\" metric in the categorization configuration \n",
        action = "store_true",
        default = False
    )
    
    parser.add_argument(
        "--location",
        help = "Location \n",
        type = str,
        required = False,
        choices = [_loc for _loc in dir(constants.LOCATION) if not _loc.startswith("__")],
    )
    
    parser.add_argument(
        "--nodb",
        help = "Will not fetch information from the database \n",
        action = "store_true",
        default = False
    )
    
    parser.add_argument(
        "--outdir",
        help = "Output directory.\n",
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
        
        #print(f"Loading SiPM information from {args.sipminfo} ...")
        d_loaded_part_info[constants.SIPM.KIND_OF_PART] = utils.load_part_info(parttype = constants.SIPM.KIND_OF_PART, yamlfile = args.sipminfo)
        #print(f"Loaded information for {len(d_loaded_part_info[constants.SIPM.KIND_OF_PART])} SiPMs.")
    
    if (args.sminfo) :
        
        #print(f"Loading SM information from {args.sminfo} ...")
        d_loaded_part_info[constants.SM.KIND_OF_PART] = utils.load_part_info(parttype = constants.SM.KIND_OF_PART, yamlfile = args.sminfo)
        #print(f"Loaded information for {len(d_loaded_part_info[constants.SM.KIND_OF_PART])} SMs.")
    
    if (args.dminfo) :
        
        #print(f"Loading DM information from {args.dminfo} ...")
        d_loaded_part_info[constants.DM.KIND_OF_PART] = utils.load_part_info(parttype = constants.DM.KIND_OF_PART, yamlfile = args.dminfo)
        #print(f"Loaded information for {len(d_loaded_part_info[constants.DM.KIND_OF_PART])} DMs.")
    
    print("Combining parts ...")
    utils.combine_parts(
        d_sipms = d_loaded_part_info[constants.SIPM.KIND_OF_PART],
        d_sms = d_loaded_part_info[constants.SM.KIND_OF_PART],
        d_dms = d_loaded_part_info[constants.DM.KIND_OF_PART],
    )
    print("Combined parts.")
    
    # Get list of modules
    print(f"Parsing {len(l_fnames)} files to get modules to process ...")
    
    l_toproc_modules = []
    l_toskip_modules = []
    l_skipped_modules = []
    l_duplicate_modules = []
    d_modules = sortedcontainers.SortedDict()
    
    for toproc in args.modules :
        
        if (os.path.isfile(toproc)) :
            
            l_tmp = numpy.loadtxt(toproc, dtype = str).flatten()
            l_toproc_modules.extend(l_tmp)
        
        else :
            
            l_toproc_modules.append(toproc)
    
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
        
        if (l_toproc_modules and barcode not in l_toproc_modules) :
            
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
    d_plotcfgs = {}
    
    if (args.plotcfg) :
        
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
    l_modules_nodata = []
    
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
                    
                    if nelements :
                        
                        # Create and store arrays of ones of specific lengths; no need to recreate them everytime
                        if nelements not in d_ones :
                            
                            d_ones[nelements] = numpy.ones(nelements)
                        
                        #print(module.barcode, plot_arr)
                        
                        entrycfg["hist"].FillN(
                            nelements,
                            plot_arr,
                            d_ones[nelements]
                        )
                    
                    l_modules_nodata.append((module, plotname, entryname))
                
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
                    
                    if (not len(plotx_arr) or not len(ploty_arr)) :
                        
                        l_modules_nodata.append((module, plotname, entryname))
                    
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
    
    
    # Save the categorization
    outfname = f"{args.outdir}/module_categorization.yaml"
    print(f"Writing categorizations to: {outfname}")
    
    with open(outfname, "w") as fopen:
        
        yaml.dump(d_cat_results, fopen)
    
    
    # Pair SMs
    if (args.pairsms) :
        
        d_cat_pairs = {}
        
        d_produced_dms = utils.save_all_part_info(
            parttype = constants.DM.KIND_OF_PART,
            outyamlfile = args.dminfo,
            inyamlfile = args.dminfo,
            location_id = vars(constants.LOCATION)[args.location],
            ret = True,
            nodb = args.nodb
        )
        
        l_used_sms = list(itertools.chain(*[[_dm.sm1, _dm.sm2] for _dm in d_produced_dms.values()]))
        
        for cat in d_cat_results["categories"].keys() :
            
            #l_sms = [{_sm: d_cat_results["results"][_sm]} for _sm in d_cat_results["modules"][cat] if _sm not in l_used_sms]
            l_sms = [{
                "barcode": _sm,
                "pairing": d_cat_results["results"][_sm]["pairing"],
            } for _sm in d_cat_results["modules"][cat] if _sm not in l_used_sms]
            #l_sms = [_sm for _sm in l_sms if _sm not in l_used_sms]
            n_sms = len(l_sms)
            
            l_sms_sorted = sorted(l_sms, key = lambda _sm: _sm["pairing"])
            
            #print()
            print(f"Finding pairs in {n_sms} category {cat} SMs ...")
            
            l_sm_groups = [l_sms_sorted[_i: _i+2] if (_i < n_sms-1) else l_sms_sorted[_i: _i+1] for _i in range(0, n_sms, 2)]
            l_sm_pairs = [sorted(_pair, key = lambda _x: int(_x["barcode"])) for _pair in l_sm_groups if len(_pair) == 2]
            
            d_cat_pairs[cat] = l_sm_pairs
            
            outfname = f"{args.outdir}/sm-pairs_cat-{cat}.csv"
            print(f"Writing pairing results to: {outfname} ...")
            with open(outfname, "w") as fopen :
                
                print("#sm1 barcode , sm2 barcode , sm1 metric , sm2 metric", file = fopen)
                for pair in l_sm_pairs :
                    
                    print(f"{pair[0]['barcode']} , {pair[1]['barcode']} , {pair[0]['pairing']:.2f} , {pair[1]['pairing']:.2f}", file = fopen)
    
    
    # Save arguments
    outfname = f"{args.outdir}/arguments.yaml"
    print(f"Writing program arguments to: {outfname} ...")
    with open(outfname, "w") as fopen:
        
        yaml.dump(vars(args), fopen)
    
    # Copy relevant files to the output directory for reference
    l_files_to_copy = [
        *args.skipmodules,
        args.plotcfg,
        args.catcfg,
        args.sipminfo,
        args.sminfo,
        args.dminfo,
    ]
    
    l_files_to_copy = [_f for _f in l_files_to_copy if _f and os.path.isfile(_f)]
    
    for fname in l_files_to_copy :
        
        print(f"Copying {fname} to {args.outdir} ...")
        os.system(f"cp {fname} {args.outdir}/")
    
    if len(l_modules_nodata) :
        
        print(f"No data found for the following {len(l_modules_nodata)} modules:")
        for module, plotname, entryname in l_modules_nodata:
            
            print(f"[barcode {module.barcode}] [plot {plotname}] [entry {entryname}]")


if __name__ == "__main__" :
    
    main()