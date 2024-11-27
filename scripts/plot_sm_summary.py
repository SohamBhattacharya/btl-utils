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
    
    #barcode: str = None
    run: int = None
    fname: str = None
    category: str = None


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots SM summary",
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
        "--plotyaml",
        help = "YAML file with plot configurations.\n   ",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--skipsms",
        help = "List of SM barcodes to skip.\n   ",
        type = str,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--skipruns",
        help = "List of SM barcodes to skip.\n   ",
        type = int,
        nargs = "+",
        required = False,
        default = [],
    )
    
    parser.add_argument(
        "--smyaml",
        help = "YAML file with SM information (such as LYSO and SiPM barcodes).\n   ",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--catyaml",
        help = "YAML file with SM categorizations..\n   ",
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
    
    rgx = re.compile(args.regexp)
    
    # Get the list of files with specified extensions
    l_fnames = []
    print(f"Getting list of files from {len(args.srcs)} source(s) ...")
    
    for src in tqdm.tqdm(args.srcs) :
        
        while "//" in src:
            
            src = src.replace("//", "/")
        
        l_tmp = glob.glob(f"{src}/**", recursive = True)
        l_tmp = [_f for _f in l_tmp if os.path.isfile(_f) and rgx.search(_f)]
        l_fnames.extend(l_tmp)
    
    d_loaded_sm_info = {}
    
    if (args.smyaml) :
        
        print("Loading SM information from {args.smyaml}")
        d_loaded_sm_info = utils.load_part_info(parttype = constants.SM.KIND_OF_PART, yamlfile = args.smyaml)
    
    # Get list of SMs
    print(f"Parsing {len(l_fnames)} files to get SMs to process ...")
    
    l_skipped_sms = []
    d_duplicate_sms = []
    d_sms = sortedcontainers.SortedDict()
    
    for fname in tqdm.tqdm(l_fnames) :
        
        parsed_result = utils.parse_string_regex(
            s = fname,
            regexp = args.regexp,
        )
        
        run = int(parsed_result["run"]) if ("run" in parsed_result) else -1
        barcode = parsed_result["barcode"].strip()
        
        if (run in args.skipruns or barcode in args.skipsms) :
            
            #print(f"Skipping SM {barcode}")
            l_skipped_sms.append(barcode)
            continue
        
        # If the SM is repeated, only use the latest run
        if (barcode in d_sms and run < d_sms[barcode].run) :
            
            d_duplicate_sms.append({"run": run, "barcode": barcode, "fname": fname})
            continue
        
        d_sms[barcode] = SensorModule(
            barcode = barcode,
            lyso = d_loaded_sm_info[barcode].lyso if barcode in d_loaded_sm_info else "0",
            sipm1 = d_loaded_sm_info[barcode].sipm1 if barcode in d_loaded_sm_info else "0",
            sipm2 = d_loaded_sm_info[barcode].sipm2 if barcode in d_loaded_sm_info else "0",
            run = run,
            fname = fname
        )
    
    print(f"Skipped {len(l_skipped_sms)} SMs:")
    print("\n".join(l_skipped_sms))
    print()
    
    print(f"Skipped {len(d_duplicate_sms)} duplicate SMs:")
    print("#Run Barcode Filename")
    for sm in d_duplicate_sms :
        
        print(f"{sm['run']} {sm['barcode'], {sm['fname']}}")
    
    print()
    
    # Read the plot config yaml
    d_plotcfgs = None
    
    with open(args.plotyaml, "r") as fopen :
        
        d_plotcfgs = yaml.load(fopen.read())
    
    # Read the category config yaml
    d_catcfgs = None
    
    with open(args.catyaml, "r") as fopen :
        
        d_catcfgs = yaml.load(fopen.read())
    
    d_cat_results = {
        "categories": d_catcfgs["categories"],
        "counts": {_key: 0 for _key in d_catcfgs["categories"].keys()},
        "modules": {_key: [] for _key in d_catcfgs["categories"].keys()},
        "results": {}
    }
    
    # Process the files
    print(f"Processing {len(d_sms)} SMs ...")
    
    d_ones = {}
    
    for sm in tqdm.tqdm(d_sms.values()) :
        
        rootfile = ROOT.TFile.Open(sm.fname)
        
        d_sm_cat = utils.eval_category(
            rootfile = rootfile,
            d_catcfgs = d_catcfgs,
            barcode = sm.barcode
        )
        
        sm_cat = d_sm_cat["category"]
        d_cat_results["counts"][sm_cat] += 1
        d_cat_results["modules"][sm_cat].append(DoubleQuotedScalarString(sm.barcode))
        d_cat_results["results"][sm.barcode] = {
            "category": DoubleQuotedScalarString(sm_cat),
            **d_sm_cat["metrics"],
            "fname": DoubleQuotedScalarString(sm.fname),
        }
        
        for plotname, plotcfg in d_plotcfgs.items() :
            
            for entryname, entrycfg in plotcfg["entries"].items() :
                
                plot_arr = None
                nelements = None
                d_fmt = {
                    "run": sm.run,
                    "barcode": sm.barcode,
                    "lyso": sm.lyso,
                    "category": sm_cat,
                }
                
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
                    
                    #if "read" in entrycfg :
                    #    
                    #    plot_str = entrycfg["plot"].format(**d_fmt)
                    #    plot_arr = numpy.array(eval(plot_str), ndmin = 1).flatten()
                    #
                    #else :
                    #    
                    #    graph = rootfile.Get(entrycfg["plot"])
                    #    plot_arr = numpy.array(graph.GetY())
                    
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
                    
                    #print("Filled")
                
                elif (plotcfg["type"] == "graph") :
                    
                    if ("graph" not in entrycfg) :
                        
                        gr_tmp = ROOT.TGraph()
                        gr_tmp.SetName(entryname)
                        gr_tmp.SetTitle(entrycfg["label"])
                        
                        #gr_tmp.SetDirectory(0)
                        #gr_tmp.SetOption(entrycfg["drawopt"])
                        #gr_tmp.GetHistogram().SetOption(entrycfg["drawopt"])
                        gr_tmp.SetLineWidth(2)
                        gr_tmp.SetLineColor(entrycfg["color"])
                        gr_tmp.SetMarkerColor(entrycfg["color"])
                        gr_tmp.SetMarkerSize(entrycfg["size"])
                        gr_tmp.SetMarkerStyle(entrycfg["marker"])
                        gr_tmp.SetFillStyle(0)
                        
                        d_plotcfgs[plotname]["entries"][entryname]["graph"] = gr_tmp
                    
                    plotx_str = entrycfg["plotx"].format(**d_fmt)
                    ploty_str = entrycfg["ploty"].format(**d_fmt)
                    
                    plotx = eval(plotx_str)
                    ploty = eval(ploty_str)
                    
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
                
                hist.SetTitle(f"{hist.GetTitle()} [#mu: {mean_str}, #sigma/#mu: {stddev/mean*100:0.2f}%]")
            
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
                gr.GetHistogram().SetOption(entrycfg["drawopt"])
                l_graphs.append(gr)
            
            utils.root_plot1D(
                #l_hist = [l_graphs[0].GetHistogram().Clone()],
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
    #    args.plotyaml,
    #    args.smyaml,
    #    args.catyaml,
    #]
    
    # Save the categorization
    outfname = f"{args.outdir}/sm_categorization.yaml"
    print(f"Writing categorizations to file ...")
    
    with open(outfname, "w") as fopen:
        
        yaml.dump(d_cat_results, fopen)
    
    print(f"Written categorizations to file: {outfname}")



if __name__ == "__main__" :
    
    main()