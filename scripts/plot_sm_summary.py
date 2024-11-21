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
import tqdm
import yaml

import utils


@dataclasses.dataclass(init = True)
class SensorModule :
    
    barcode: str = None
    run: int = None
    fname: str = None


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
        "--cfg",
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
    
    with open(args.cfg, "r") as fopen :
        
        d_plotcfgs = yaml.load(fopen.read(), Loader = yaml.FullLoader)
        #d_plotcfgs = utils.dict_to_obj(d_plotcfgs)
    
    # Process the files
    print(f"Processing {len(d_sms)} SMs ...")
    
    d_ones = {}
    
    for sm in tqdm.tqdm(d_sms.values()) :
        
        rootfile = ROOT.TFile.Open(sm.fname)
        
        for plotname, plotcfg in d_plotcfgs.items() :
            
            for entryname, entrycfg in plotcfg["entries"].items() :
                
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
                
                plot_arr = None
                nelements = None
                
                if "read" in entrycfg :
                    
                    d_arr_y = {}
                    d_fmt = {}
                    
                    for varkey, varname in entrycfg["read"].items() :
                        
                        graph = rootfile.Get(varname)
                        d_arr_y[varkey] = numpy.array(graph.GetY())
                        d_fmt[varkey] = f"d_arr_y['{varkey}']"
                    
                    plot_str = entrycfg["plot"].format(**d_fmt)
                    plot_arr = numpy.array(eval(plot_str), ndmin = 1).flatten()
                
                else :
                    
                    graph = rootfile.Get(entrycfg["plot"])
                    plot_arr = numpy.array(graph.GetY())
                
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
        
        rootfile.Close()
    
    for plotname, plotcfg in d_plotcfgs.items() :
        
        l_hists = [_entrycfg["hist"] for _entrycfg in plotcfg["entries"].values()]
        
        for hist in l_hists :
            
            utils.handle_flows(hist)
            
            mean = hist.GetMean()
            mean_str = f"{round(mean)}" if mean > 100 else f"{mean:0.2f}"
            rms = hist.GetRMS()
            
            hist.SetTitle(f"{hist.GetTitle()} [mean: {mean_str}, RMS: {rms/mean*100:0.2f}%]")
        
        utils.root_plot1D(
            l_hist = l_hists,
            outfile = f"{args.outdir}/{plotname}.pdf",
            xrange = (plotcfg["xmin"], plotcfg["xmax"]),
            yrange = (0.5, 10 * max([_hist.GetMaximum() for _hist in l_hists])),
            ratio_num_den_pairs = [],
            l_hist_overlay = [],
            l_graph_overlay = [],
            gr_overlay_drawopt = "PE1",
            ratio_mode = "mc",
            no_xerror = False,
            logx = False,
            logy = True,
            title = "",
            xtitle = plotcfg["xtitle"],
            ytitle = plotcfg["ytitle"],
            centertitlex = True,
            centertitley = True,
            gridx = plotcfg["gridx"],
            gridy = plotcfg["gridy"],
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



if __name__ == "__main__" :
    
    main()