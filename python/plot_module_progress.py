#!/usr/bin/env python3

import argparse
import numpy
import os
import ROOT

from datetime import datetime
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from statsmodels.tsa.statespace.sarimax import SARIMAX

import constants
import utils
from utils import yaml


LOC_ALL = "ALL"

TOTALS = {
    constants.SM.KIND_OF_PART: {
        "CIT": 18*144,
        "MIB": 18*144,
        "PKU": 18*144,
        "UVA": 18*144,
        LOC_ALL: 72*144,
    },
    constants.DM.KIND_OF_PART: {
        "CIT": 18*72,
        "MIB": 18*72,
        "PKU": 18*72,
        "UVA": 18*72,
        LOC_ALL: 72*72,
    },
}

def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class = utils.Formatter,
        description = "Plots module gluing/assembly progress",
    )
    
    #parser.add_argument(
    #    "--info",
    #    help = "Module type.\n",
    #    type = str,
    #    nargs = "*",
    #    required = False,
    #    choices = [constants.SM.KIND_OF_PART, constants.DM.KIND_OF_PART]
    #)
    
    parser.add_argument(
        "--moduletypes",
        help = "Module type(s).\n",
        type = str,
        nargs = "*",
        required = True,
        choices = [constants.SM.KIND_OF_PART, constants.DM.KIND_OF_PART]
    )
    
    parser.add_argument(
        "--locations",
        help = "Location(s)\n",
        type = str,
        nargs = "*",
        required = False,
        choices = [_loc for _loc in dir(constants.LOCATION) if not _loc.startswith("__")],
    )
    
    parser.add_argument(
        "--outdir",
        help = "Output directory.\n",
        type = str,
        required = True,
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    d_module_info = {}
    d_module_hist = {}
    d_module_time = {}
    
    time_min = numpy.inf
    time_max = -1
    
    for mtype in args.moduletypes :
        
        d_module_info[mtype] = {}
        d_module_time[mtype] = {}
        
        for loc in args.locations :
            
            fname_info = f"{args.outdir}/info_{mtype}_{loc}.yaml"
            
            d_module_info[mtype][loc] = utils.save_all_part_info(
                parttype = mtype,
                outyamlfile = fname_info,
                inyamlfile = fname_info,
                location_id = getattr(constants.LOCATION, loc),
                ret = True
            )
            
            d_module_time[mtype][loc] = numpy.array([
                ROOT.TDatime(_module.prod_datime).Convert(toGMT = True)
                for _module in d_module_info[mtype][loc].values()
                if _module and _module.prod_datime and _module.barcode.startswith("321100")
            ], dtype = float)
            
            time_min = min(time_min, min(d_module_time[mtype][loc]))
            time_max = max(time_max, max(d_module_time[mtype][loc]))
    
    nsecs_day = 3600*24
    time_min = nsecs_day * numpy.floor(time_min/nsecs_day)
    time_max = nsecs_day * numpy.ceil(time_max/nsecs_day)
    nbins = int((time_max - time_min)/nsecs_day)
    
    time_start = time_min
    time_end = time_start + (365*nsecs_day)
    
    for mtype in args.moduletypes :
        
        d_module_hist[mtype] = {}
        d_module_hist[mtype][LOC_ALL] = {}
        d_module_hist[mtype][LOC_ALL]["hist"] = ROOT.TH1F(f"h1_{mtype}_{LOC_ALL}", "All", nbins, time_min, time_max)
        
        for loc in args.locations :
            
            histname = f"h1_{mtype}_{loc}"
            d_module_hist[mtype][loc] = {}
            d_module_hist[mtype][loc]["hist"] = ROOT.TH1F(histname, loc, nbins, time_min, time_max)
            
            arr_time = d_module_time[mtype][loc]
            
            d_module_hist[mtype][loc]["hist"].FillN(
                len(arr_time),
                arr_time,
                numpy.ones(len(arr_time))
            )
            
            d_module_hist[mtype][loc]["total"] = int(d_module_hist[mtype][loc]["hist"].Integral())
            
            d_module_hist[mtype][LOC_ALL]["hist"].Add(d_module_hist[mtype][loc]["hist"])
            d_module_hist[mtype][loc]["hist_cumu"] = d_module_hist[mtype][loc]["hist"].GetCumulative()
            #d_module_hist[mtype][loc]["hist_cumu"].Scale(1.0/TOTALS[mtype][loc])
            
            d_module_hist[mtype][loc]["hist_cumu"].SetTitle(f"{loc} ({d_module_hist[mtype][loc]['total']}/{TOTALS[mtype][loc]})")
            d_module_hist[mtype][loc]["hist_cumu"].SetLineStyle(7)
            d_module_hist[mtype][loc]["hist_cumu"].SetLineWidth(2)
            d_module_hist[mtype][loc]["hist_cumu"].SetLineColor(getattr(constants.COLORS, loc))
            d_module_hist[mtype][loc]["hist_cumu"].SetOption("hist")
            d_module_hist[mtype][loc]["hist_cumu"].SetMarkerSize(0)
            d_module_hist[mtype][loc]["hist_cumu"].SetFillStyle(0)
        
        d_module_hist[mtype][LOC_ALL]["total"] = int(d_module_hist[mtype][LOC_ALL]["hist"].Integral())
        
        d_module_hist[mtype][LOC_ALL]["hist_cumu"] = d_module_hist[mtype][LOC_ALL]["hist"].GetCumulative()
        #d_module_hist[mtype][LOC_ALL]["hist_cumu"].Scale(1.0/TOTALS[mtype][LOC_ALL])
        
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetTitle(f"{LOC_ALL} ({d_module_hist[mtype][LOC_ALL]['total']}/{TOTALS[mtype][LOC_ALL]})")
        #d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineStyle(7)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineWidth(2)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineColor(getattr(constants.COLORS, LOC_ALL))
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetOption("hist")
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetMarkerSize(0)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetFillStyle(0)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetMarkerSize(0)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].Fit("pol1", option = "SEM", goption = "L")
        
        l_hists = [d_module_hist[mtype][_loc]["hist_cumu"] for _loc in args.locations+[LOC_ALL]]
        
        outfile_csv = f"{args.outdir}/progress_{mtype}.csv"
        
        l_locations = args.locations+[LOC_ALL]
        
        arr_data = numpy.array([[
            datetime.fromtimestamp(int(d_module_hist[mtype][LOC_ALL]["hist_cumu"].GetBinCenter(_ibin+1))).strftime("%Y-%m-%d"),
            *[str(d_module_hist[mtype][_loc]["hist"].GetBinContent(_ibin+1)) for _loc in l_locations]
        ] for _ibin in range(nbins)], dtype = str)
        
        print(f"Saving data to: {outfile_csv}")
        numpy.savetxt(outfile_csv, arr_data, fmt = "%s", delimiter = " , ", header = " , ".join(["Date"] + l_locations))
        
        #for hist in l_hists :
        #    
        #    hist.Scale(1.0/1000)
        
        for loc in l_locations :
            
            d_module_hist[mtype][loc]["hist_cumu"].Scale(1.0/TOTALS[mtype][loc])
        
        #ROOT.TGaxis.SetMaxDigits(2)
        mtype_label = "SM" if mtype == constants.SM.KIND_OF_PART else "DM"
        
        # Forcast
        # https://builtin.com/data-science/time-series-forecasting-python
        # https://www.statsmodels.org/stable/examples/notebooks/generated/statespace_forecasting.html
        
        arr_data_train = numpy.array([
            d_module_hist[mtype][LOC_ALL]["hist_cumu"].GetBinContent(_ibin+1)
        for _ibin in range(nbins)])
        
        mod = SARIMAX(arr_data_train, order=(5, 4, 2), trend='c')
        
        utils.root_plot1D(
            l_hist = l_hists,
            outfile = f"{args.outdir}/progress_{mtype}.pdf",
            xrange = (time_min, time_max),
            #xrange = (time_start, time_end),
            #yrange = (0, 1.2 * max([_hist.GetMaximum() for _hist in l_hists])),
            yrange = (0, 1.1),
            logx = False,
            logy = False,
            xtitle = "Date",
            ytitle = f"Cumulative {mtype_label} fraction",
            timeformatx = "#lower[0.3]{#splitline{%Y}{%d/%m}}",
            gridx = True,
            gridy = True,
            ndivisionsx = (4, 1, 0),
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
        
    #print(d_module_info)
    
    
    return 0


if __name__ == "__main__" :
    
    main()