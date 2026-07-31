#!/usr/bin/env python3

import argparse
import copy
import itertools
import os
import numpy
import tqdm
import pprint

import ROOT
ROOT.gROOT.SetBatch(True)

import utils
from utils import yaml
from utils import logging
from utils import get_grx
from utils import get_gry
import constants


def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Find QAQC runs for modules from external BACs",
    )
    
    parser.add_argument(
        "--srcs",
        help = (
            "Source directories and regular expressions for each location/BAC: BAC1:dir1:regexp1 BAC2:dir1:regexp2 ...\n"
            "Only files that match the regular expression will be processed.\n"
            "regexp is a keyed regular expression, used to extract run and barcode from the file name.\n"
            "SM example (for cases like \"runXXXX/module_YYYY_analysis.root\"): \"run(?P<run>\\d+)/module_(?P<barcode>\\d+)_analysis.*.root\"\n"
            "\n"
        ),
        type = str,
        nargs = "+",
        required = True,
    )
    
    parser.add_argument(
        "--plotcfg",
        help = "YAML file with plot configurations.\n",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--outdir",
        help = "Output directory.\n",
        type = str,
        required = True,
    )
    
    args = parser.parse_args()
    
    l_valid_locations = utils.get_valid_locations()
    
    d_src_info = {}
    l_all_barcodes = []
    
    for argsrc in args.srcs :
        
        loc, src, regexp = argsrc.split(":")
        
        assert loc in l_valid_locations, f"{loc} is not a valid location. Valid locations: {', '.join(l_valid_locations)}"
        
        if loc not in d_src_info :
            d_src_info[loc] = {}
        
        l_fnames, l_regexps = utils.get_file_list(l_srcs = [src], l_regexps = [regexp])
        
        for fname, regexp in zip(l_fnames, l_regexps) :
            
            parsed_result = utils.parse_string_regex(
                s = fname,
                regexp = regexp,
            )
            
            #run = int(parsed_result["run"]) if ("run" in parsed_result) else -1
            barcode = parsed_result["barcode"].strip()
            
            #if barcode not in ["32110020000547"] :
            #    continue
            
            #if loc == "CIT" and barcode == "32110020000547" :
            #    continue
            
            print(f"BAC: {loc}, Barcode: {barcode}, File: {fname}")
            
            d_src_info[loc][barcode] = fname
            
            if barcode not in l_all_barcodes :
                l_all_barcodes.append(barcode)
    
    l_all_barcodes = utils.natural_sort(l_all_barcodes)
    
    l_locations = utils.natural_sort(d_src_info.keys())
    d_loc_barcodes = {_loc: [] for _loc in l_locations}
    
    for loc in l_locations :
        
        barcode_ranges = getattr(constants, "SM").BARCODE_RANGES[utils.get_location_id(loc)]
        
        for barcode in l_all_barcodes :
            
            cond_str = " or ".join([
                f"({barcode} > {_range[0]} and {barcode} < {_range[1]})" for _range in barcode_ranges
            ])
            
            if eval(cond_str) :
                d_loc_barcodes[loc].append(barcode)
    
    d_barcode_cfg = {_bc: {} for _bc in l_all_barcodes}
    
    for iloc, loc in enumerate(l_locations) :
        
        for ibc, barcode in enumerate(d_loc_barcodes[loc]) :
            
            d_barcode_cfg[barcode] = {
                "color": utils.get_cms_colors(ibc),
                "marker": utils.get_marker_style(iloc),
                "label": f"{int(barcode)-32110020000000:05d} ({loc})",
            }
    
    d_plotcfgs = {}
    with open(args.plotcfg, "r") as fopen :
        
        d_plotcfgs = yaml.load(fopen.read())
    
    #l_loc_pairs = list(itertools.combinations(l_locations, 2))
    l_loc_pairs = list(itertools.permutations(l_locations, 2))
    d_loc_info = {_key: {"plotcfgs": copy.deepcopy(d_plotcfgs)} for _key in l_loc_pairs}
    
    for p_loc in l_loc_pairs :
        
        loc1, loc2 = p_loc
        d_loc_info[p_loc]["barcodes"] = utils.natural_sort(list(set(d_src_info[loc1].keys()) & set(d_src_info[loc2].keys())))
    
    #pprint.pprint(d_loc_info)
    
    for p_loc in d_loc_info.keys() :
        
        l_barcodes = d_loc_info[p_loc]["barcodes"]
        
        if not l_barcodes :
            logging.warning(f"No common barcodes found for locations: {p_loc}. Skipping.")
            continue
        
        loc_x, loc_y = p_loc
        d_plotcfgs_loc = d_loc_info[p_loc]["plotcfgs"]
        
        for barcode in l_barcodes :
            
            fname_x = d_src_info[loc_x][barcode]
            fname_y = d_src_info[loc_y][barcode]
            
            rootfile_x =  ROOT.TFile.Open(fname_x)
            rootfile_y =  ROOT.TFile.Open(fname_y)
            
            for plotname, plotcfg in d_plotcfgs_loc.items() :
                
                d_loc_info[p_loc][plotname] = {}
                
                for entryname, entrycfg in plotcfg["entries"].items() :
                    
                    if (isinstance(entrycfg["color"], str) and entrycfg["color"].startswith("#")) :
                        
                        entrycfg["color"] = ROOT.TColor.GetColor(entrycfg["color"])
                    
                    if ("graph" not in entrycfg) :
                        
                        entrycfg["graph"] = {}
                        
                        gr_tmp = ROOT.TGraph()
                        gr_tmp.SetName(entryname)
                        gr_tmp.SetTitle(entrycfg["label"])
                        
                        gr_tmp.SetLineWidth(2)
                        gr_tmp.SetLineColor(entrycfg["color"])
                        gr_tmp.SetMarkerColor(entrycfg["color"])
                        gr_tmp.SetMarkerSize(entrycfg["size"])
                        gr_tmp.SetMarkerStyle(entrycfg["marker"])
                        gr_tmp.SetFillStyle(0)
                        
                        #entrycfg["graph"] = gr_tmp
                        entrycfg["graph"]["all"] = gr_tmp
                    
                    if barcode not in entrycfg["graph"] :
                        
                        gr_tmp = ROOT.TGraph()
                        gr_tmp.SetName(f"{entryname}_{barcode}")
                        gr_tmp.SetTitle(d_barcode_cfg[barcode]["label"])
                        
                        gr_tmp.SetLineWidth(2)
                        gr_tmp.SetLineColor(d_barcode_cfg[barcode]["color"])
                        gr_tmp.SetMarkerColor(d_barcode_cfg[barcode]["color"])
                        #gr_tmp.SetMarkerSize(entrycfg["size"])
                        gr_tmp.SetMarkerSize(2)
                        gr_tmp.SetMarkerStyle(d_barcode_cfg[barcode]["marker"])
                        gr_tmp.SetFillStyle(0)
                        entrycfg["graph"][barcode] = gr_tmp
                    
                    plotx_arr = None
                    ploty_arr = None
                    #nelements = None
                    
                    d_fmt_x = {"loc": loc_x}
                    d_fmt_y = {"loc": loc_y}
                    d_read_info_x = {}
                    d_read_info_y = {}
                    
                    for varkey, varname in entrycfg.get("readx", {}).items() :
                        
                        d_read_info_x[varkey] = rootfile_x.Get(varname)
                        d_fmt_x[varkey] = f"d_read_info_x['{varkey}']"
                    
                    for varkey, varname in entrycfg.get("ready", {}).items() :
                        
                        d_read_info_y[varkey] = rootfile_y.Get(varname)
                        d_fmt_y[varkey] = f"d_read_info_y['{varkey}']"
                    
                    for defkey, defexpr in entrycfg.get("defx", {}).items() :
                        
                        defexpr = defexpr.format(**d_fmt_x)
                        d_fmt_x[defkey] = defexpr
                    
                    for defkey, defexpr in entrycfg.get("defy", {}).items() :
                        
                        defexpr = defexpr.format(**d_fmt_y)
                        d_fmt_y[defkey] = defexpr
                    
                    plotx_str = entrycfg["plotx"].format(**d_fmt_x)
                    ploty_str = entrycfg["ploty"].format(**d_fmt_y)
                    
                    print(f"plotx_str: {plotx_str}")
                    print(f"ploty_str: {ploty_str}")
                    
                    try:
                        plotx_arr = eval(plotx_str)
                        ploty_arr = eval(ploty_str)
                    except Exception as excpt:
                        print(excpt)
                        raise
                    
                    #print(plotx_arr)
                    #print(ploty_arr)
                    
                    #mean_x = numpy.mean(plotx_arr)
                    #mean_y = numpy.mean(ploty_arr)
                    
                    #print(p_loc)
                    #pprint.pprint(numpy.dstack((plotx_arr, ploty_arr))[0])
                    
                    for plotx, ploty in numpy.dstack((plotx_arr, ploty_arr))[0] :
                        
                        ## Move the outliers to the outer range
                        #plotx = max(plotcfg["xmin"], plotx) if (plotcfg["xmin"] is not None) else plotx
                        #plotx = min(plotcfg["xmax"], plotx) if (plotcfg["xmax"] is not None) else plotx
                        #
                        #ploty = max(plotcfg["ymin"], ploty) if (plotcfg["ymin"] is not None) else ploty
                        #ploty = min(plotcfg["ymax"], ploty) if (plotcfg["ymax"] is not None) else ploty
                        
                        entrycfg["graph"]["all"].AddPoint(plotx, ploty)
                        entrycfg["graph"][barcode].AddPoint(plotx, ploty)
            
            rootfile_x.Close()
            rootfile_y.Close()
        
        
        for plotname, plotcfg in d_plotcfgs_loc.items() :
            
            l_graphs = []
            
            xmin = plotcfg["xmin"]
            xmax = plotcfg["xmax"]
            
            ymin = plotcfg["ymin"]
            ymax = plotcfg["ymax"]
            
            for entryname, entrycfg in plotcfg["entries"].items() :
                
                gr = entrycfg["graph"]["all"]
                
                #mean_x_all = gr.GetMean(1)
                #mean_y_all = gr.GetMean(2)
                #
                #gr.Scale(1.0/mean_x_all, "x")
                #gr.Scale(1.0/mean_y_all, "y")
                
                labelmode = plotcfg.get("labelmode", None)
                
                if (labelmode == "corr") :
                    
                    corr = numpy.corrcoef(get_grx(gr), get_gry(gr))[0, 1]*100
                    #corr_str = f"{corr:0.2g}"
                    gr.SetTitle(f"{gr.GetTitle()}#scale[0.7]{{ [#rho: {corr:0.2g}%]}}")
                
                for fnname, fnstr in entrycfg.get("fit", {}).items() :
                    
                    xmin_fn = min(numpy.array(gr.GetX()))
                    xmax_fn = max(numpy.array(gr.GetX()))
                    
                    f1 = ROOT.TF1(fnname, fnstr, xmin_fn, xmax_fn)
                    f1.SetLineWidth(2)
                    f1.SetLineStyle(7)
                    f1.SetLineColor(entrycfg["color"])
                    
                    fit_res = gr.Fit(
                        f1,
                        option = "SEM",
                        goption = "L",
                        xmin = xmin_fn,
                        xmax = xmax_fn
                    )
                    
                    #fn_fitted = gr.GetListOfFunctions().FindObject(fnname)
                    #fn_fitted.SetLineColor(entrycfg["color"])
                    #fn_fitted.SetLineWidth(2)
                    #fn_fitted.SetLineStyle(7)
                    #fn_fitted.SetMarkerSize(0)
                    #print("Fitted")
                    
                    fn_expr_str = utils.root_get_fn_expr(f1, "0.2g")
                    gr.SetTitle(f"{gr.GetTitle()}#scale[0.8]{{ [ y={fn_expr_str} ]}}")
                
                gr.SetTitle(f"#splitline{{"
                    f"{gr.GetTitle()}}}"
                    f"{{#scale[0.8]{{"
                        f"#splitline{{"
                                f"#mu_{{x|y}}={gr.GetMean(1):0.2g}|{gr.GetMean(2):0.2g}, "
                                f"#sigma_{{x|y}}={gr.GetRMS(1):0.2g}|{gr.GetRMS(2):0.2g}"
                            f"}}{{"
                                f"r = {gr.GetCorrelationFactor():0.2g}"
                            f"}}"
                    f"}}"
                f"}}")
                
                gr.GetHistogram().SetOption(entrycfg["drawopt"])
                l_graphs.append(gr)
                
                for bc in l_barcodes :
                    
                    gr_bc = entrycfg["graph"][bc]
                    
                    #gr_bc.Scale(1.0/mean_x_all, "x")
                    #gr_bc.Scale(1.0/mean_y_all, "y")
                    
                    gr_bc.GetHistogram().SetOption(entrycfg["drawopt"])
                    gr_bc.SetTitle(f"#splitline{{"
                        f"{gr_bc.GetTitle()}}}"
                        f"{{#scale[0.75]{{"
                            f"#splitline{{"
                                f"#mu_{{x|y}}={gr_bc.GetMean(1):0.2g}|{gr_bc.GetMean(2):0.2g}, "
                                f"#sigma_{{x|y}}={gr_bc.GetRMS(1):0.2g}|{gr_bc.GetRMS(2):0.2g}"
                            f"}}{{"
                                f"r = {gr_bc.GetCorrelationFactor():0.2g}"
                            f"}}"
                        f"}}"
                    f"}}")
                    
                    l_graphs.append(gr_bc)
                
                arr_x_tmp = numpy.array(gr.GetX())
                arr_y_tmp = numpy.array(gr.GetY())
                
                if plotcfg["xmin"] is None :
                    
                    xmin = min(xmin, min(arr_x_tmp)) if xmin is not None else min(arr_x_tmp)
                
                if plotcfg["xmax"] is None :
                    
                    xmax = max(xmax, max(arr_x_tmp)) if xmax is not None else max(arr_x_tmp)
                
                if plotcfg["ymin"] is None :
                    
                    ymin = min(ymin, min(arr_y_tmp)) if ymin is not None else min(arr_y_tmp)
                
                if plotcfg["ymax"] is None :
                    
                    ymax = max(ymax, max(arr_y_tmp)) if ymax is not None else max(arr_y_tmp)
            
            legendncol = 3
            
            #print(xmin, xmax, ymin, ymax)
            #exit()
            
            dxrange = xmax - xmin
            dyrange = ymax - ymin
            scale_xmin = 0.2
            scale_xmax = 0.2
            scale_ymin = 0.2
            scale_ymax = 0.5 * numpy.ceil(len(l_graphs)/legendncol)
            #print(scale_ymax)
            
            if xmin != plotcfg["xmin"] :
                xmin -= scale_xmin*dxrange
                xmin = float(f"{xmin:0.4g}")
            if xmax != plotcfg["xmax"] :
                xmax += scale_xmax*dxrange
                xmax = float(f"{xmax:0.4g}")
            if ymin != plotcfg["ymin"] :
                ymin -= scale_ymin*dyrange
                ymin = float(f"{ymin:0.4g}")
            if ymax != plotcfg["ymax"] :
                ymax += scale_ymax*dyrange
                ymax = float(f"{ymax:0.4g}")
            
            #if plotcfg["xmin"] is None and abs(xmin) > 100:
            #    
            #    xmin = 100*(numpy.floor(xmin/100)-1)
            #
            #if plotcfg["xmax"] is None and abs(xmax) > 100:
            #    
            #    xmax = 100*(numpy.ceil(xmax/100)+1)
            #
            #if plotcfg["ymin"] is None and abs(ymin) > 100:
            #    
            #    ymin = 100*(numpy.floor(ymin/100)-1)
            #
            #if plotcfg["ymax"] is None and abs(ymax) > 100:
            #    
            #    ymax = 100*(numpy.ceil(ymax/100)+1)
            
            # Create output directory
            outdir = f"{args.outdir}/{loc_x}_{loc_y}"
            os.system(f"mkdir -p {outdir}")
            
            utils.root_plot1D(
                l_hist = [ROOT.TH1F(f"h1_tmp_{plotname}_{'_'.join(p_loc)}", "", 1, xmin, xmax)],
                outfile = f"{outdir}/{plotname}_{'_'.join(p_loc)}.pdf",
                xrange = (xmin, xmax),
                yrange = (ymin, ymax),
                l_graph_overlay = l_graphs,
                logx = plotcfg.get("logx", False),
                logy = plotcfg.get("logy", False),
                xtitle = f"{plotcfg['xtitle']} | {loc_x}",
                ytitle = f"{plotcfg['ytitle']} | {loc_y}",
                gridx = plotcfg.get("gridx", True),
                gridy = plotcfg.get("gridy", True),
                ndivisionsx = plotcfg.get("ndivisionsx", None),
                ndivisionsy = plotcfg.get("ndivisionsy", None),
                centerlabelx = plotcfg.get("centerlabelx", False),
                centerlabely = plotcfg.get("centerlabely", False),
                stackdrawopt = "nostack",
                legendpos = plotcfg.get("legendpos", "UL"),
                legendncol = legendncol,
                legendfillstyle = 0,
                legendfillcolor = 0,
                legendtextsize = 0.0275,
                #legendpadtop_extra = 0.07,
                legendpadleft_extra = 0.0,
                legendtitle = plotcfg.get("legendtitle", ""),
                legendheightscale = 1.3,
                legendwidthscale = 1.9,
                CMSextraText = "BTL Internal",
                lumiText = "Phase-2"
            )
    
    return 0


if __name__ == "__main__":
    main()