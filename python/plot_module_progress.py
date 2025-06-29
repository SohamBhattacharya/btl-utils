#!/usr/bin/env python3

import argparse
import numpy
import os
import pandas
import ROOT

from datetime import datetime
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.ar_model import AutoReg, ar_select_order

import constants
import utils
from utils import yaml


DATIME_FMT = "%Y-%m-%d %H:%M:%S%z"

LOC_ALL = "ALL"
LOC_ALL_LABEL = "All"

LOC_BACS = ["CIT", "MIB", "PKU", "UVA"]

TOTALS = {
    constants.SM.KIND_OF_PART: {
        "CIT": 18*144,
        "MIB": 18*144,
        "PKU": 18*144,
        "UVA": 18*144,
        "CERN": 18*144,
        LOC_ALL: 72*144,
    },
    constants.DM.KIND_OF_PART: {
        "CIT": 18*72,
        "MIB": 18*72,
        "PKU": 18*72,
        "UVA": 18*72,
        "CERN": 18*72,
        LOC_ALL: 72*72,
    },
}

BARCODE_RANGES = {
    constants.SM.KIND_OF_PART: {
        "MIB": (32110020000001, 32110020002800),
        "PKU": (32110020002801, 32110020005600),
        "UVA": (32110020005601, 32110020008400),
        "CIT": (32110020008401, 32110020011200),
    },
    constants.DM.KIND_OF_PART: {
        "MIB": (32110040000001, 32110040001400),
        "PKU": (32110040001401, 32110040002800),
        "UVA": (32110040002801, 32110040004200),
        "CIT": (32110040004201, 32110040005600),
    },
}


def datime_str_to_stamp(datime_str) :
    
    # +01:00 is the timezone offset for CERN
    stamp = datetime.strptime(f"{datime_str}+01:00", DATIME_FMT).timestamp()
    
    return stamp

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
    
    d_time_max = {}
    
    for mtype in args.moduletypes :
        
        d_module_info[mtype] = {}
        d_module_time[mtype] = {}
        
        d_module_info[mtype][LOC_ALL] = {}
        
        for loc in args.locations :
            
            fname_info = f"{args.outdir}/info_{mtype}_{loc}.yaml"
            
            d_module_info[mtype][loc] = utils.save_all_part_info(
                parttype = mtype,
                outyamlfile = fname_info,
                inyamlfile = fname_info,
                location_id = getattr(constants.LOCATION, loc),
                ret = True
            )
            
            d_module_info[mtype][LOC_ALL].update(d_module_info[mtype][loc])
        
        # Assembly location can be different from the current location
        # Get the assembly location using the barcode
        for loc in LOC_BACS :
            
            l_barcodes_loc = [
                _module.barcode for _module in d_module_info[mtype][LOC_ALL].values()
                if _module and _module.prod_datime and (BARCODE_RANGES[mtype][loc][0] <= int(_module.barcode) <= BARCODE_RANGES[mtype][loc][1])
            ]
            
            #d_module_time[mtype][loc] = numpy.array([
            #    ROOT.TDatime(_module.prod_datime).Convert(toGMT = True)
            #    for _module in d_module_info[mtype][loc].values()
            #    if _module and _module.prod_datime and _module.barcode.startswith("321100")
            #], dtype = float)
            
            d_module_time[mtype][loc] = numpy.array([
                #ROOT.TDatime(_module.prod_datime).Convert(toGMT = True)
                datime_str_to_stamp(_module.prod_datime)
                for _module in d_module_info[mtype][LOC_ALL].values()
                if _module and _module.barcode in l_barcodes_loc
            ], dtype = float)
            
            time_min = min(time_min, min(d_module_time[mtype][loc]))
            time_max = max(time_max, max(d_module_time[mtype][loc]))
        
        d_time_max[mtype] = time_max
    
    nsecs_day = 3600*24
    time_min = nsecs_day * numpy.floor(time_min/nsecs_day)
    time_max = nsecs_day * numpy.ceil(time_max/nsecs_day)
    nbins = int((time_max - time_min)/nsecs_day)
    
    time_start = time_min
    #time_end = time_start + (365*nsecs_day)
    # Start prediction from N months before the latest data
    time_pred_start = time_max - (60*nsecs_day)
    time_end_str = "2025-12-31 00:00:00"
    #time_end = ROOT.TDatime(time_end_str).Convert(toGMT = True)
    time_end =  datime_str_to_stamp(time_end_str)
    
    for mtype in args.moduletypes :
        
        d_module_hist[mtype] = {}
        d_module_hist[mtype][LOC_ALL] = {}
        d_module_hist[mtype][LOC_ALL]["hist"] = ROOT.TH1F(f"h1_{mtype}_{LOC_ALL}", "All", nbins, time_min, time_max)
        
        for loc in LOC_BACS :
            
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
            d_module_hist[mtype][loc]["hist_cumu"].SetOption("hist ][")
            d_module_hist[mtype][loc]["hist_cumu"].SetMarkerSize(0)
            d_module_hist[mtype][loc]["hist_cumu"].SetFillStyle(0)
        
        d_module_hist[mtype][LOC_ALL]["total"] = int(d_module_hist[mtype][LOC_ALL]["hist"].Integral())
        
        d_module_hist[mtype][LOC_ALL]["hist_cumu"] = d_module_hist[mtype][LOC_ALL]["hist"].GetCumulative()
        #d_module_hist[mtype][LOC_ALL]["hist_cumu"].Scale(1.0/TOTALS[mtype][LOC_ALL])
        
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetTitle(f"{LOC_ALL_LABEL} ({d_module_hist[mtype][LOC_ALL]['total']}/{TOTALS[mtype][LOC_ALL]})")
        #d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineStyle(7)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineWidth(2)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetLineColor(getattr(constants.COLORS, LOC_ALL))
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetOption("hist ][")
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetMarkerSize(0)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetFillStyle(0)
        d_module_hist[mtype][LOC_ALL]["hist_cumu"].SetMarkerSize(0)
        #d_module_hist[mtype][LOC_ALL]["hist_cumu"].Fit("pol1", option = "SEM", goption = "L")
        
        l_hists = [d_module_hist[mtype][_loc]["hist_cumu"] for _loc in LOC_BACS+[LOC_ALL]]
        
        l_locations = LOC_BACS+[LOC_ALL]
        
        arr_data = numpy.array([[
            datetime.fromtimestamp(int(d_module_hist[mtype][LOC_ALL]["hist_cumu"].GetBinCenter(_ibin+1))).strftime("%Y-%m-%d"),
            *[str(d_module_hist[mtype][_loc]["hist"].GetBinContent(_ibin+1)) for _loc in l_locations]
        ] for _ibin in range(nbins)], dtype = str)
        
        outfile_csv = f"{args.outdir}/progress_{mtype}.csv"
        print(f"Saving data to: {outfile_csv}")
        numpy.savetxt(outfile_csv, arr_data, fmt = "%s", delimiter = " , ", header = " , ".join(["Date"] + l_locations))
        
        for loc in l_locations :
            
            d_module_hist[mtype][loc]["hist_cumu"].Scale(1.0/TOTALS[mtype][loc])
        
        
        f1 = ROOT.TF1(f"pol1_{mtype}", "pol1", time_pred_start, time_end)
        
        fit_res = d_module_hist[mtype][LOC_ALL]["hist_cumu"].Fit(
            f1,
            option = "SW",
            goption = "LSAME",
            xmin = time_pred_start,
            xmax = time_max
        )
        f1.SetTitle("Projection (linear)")
        f1.SetFillStyle(0)
        f1.SetLineColor(12)
        f1.SetLineWidth(2)
        f1.SetLineStyle(2)
        f1.SetMarkerSize(0)
        f1.SetMarkerColor(0)
        f1.GetHistogram().SetMarkerSize(0)
        f1.GetHistogram().SetMarkerColor(0)
        f1.GetHistogram().SetOption("LSAME")
        
        #ROOT.TGaxis.SetMaxDigits(2)
        mtype_label = "SM" if mtype == constants.SM.KIND_OF_PART else "DM"
        
        # Forecast
        # https://builtin.com/data-science/time-series-forecasting-python
        # https://www.statsmodels.org/stable/examples/notebooks/generated/statespace_forecasting.html
        # https://www.statsmodels.org/stable/examples/notebooks/generated/tsa_dates.html
        
        pseries_data = pandas.Series(
            data = numpy.array([d_module_hist[mtype][LOC_ALL]["hist_cumu"].GetBinContent(_ibin+1) for _ibin in range(nbins)]),
            index = pandas.to_datetime(arr_data[:, 0]),
            copy = True
        )
        
        date_range = pandas.date_range(start = pseries_data.index.min(), end = pseries_data.index.max(), freq = "D")
        pseries_data = pseries_data.reindex(date_range, fill_value = 0)
        
        selection_res = ar_select_order(pseries_data, maxlag = 15, seasonal = False, trend = "ct")
        pandas_ar_res = selection_res.model.fit()
        
        pred_res = pandas_ar_res.predict(
            start = datetime.fromtimestamp(time_pred_start).strftime("%Y-%m-%d"),
            end = datetime.fromtimestamp(time_end).strftime("%Y-%m-%d")
        )
        #arr_pred_time = numpy.array([ROOT.TDatime(str(_dt)).Convert(toGMT = True) for _dt in pred_res.index], dtype = float)
        arr_pred_time = numpy.array([datime_str_to_stamp(_dt) for _dt in pred_res.index], dtype = float)
        arr_pred_val = numpy.array(pred_res.values, dtype = float)
        
        # Used to set the xrange
        h1_dummy = ROOT.TH1F(f"h1_dummy_{mtype}", "", 1, time_start, time_end)
        
        g1_projection = ROOT.TGraph(len(arr_pred_time), arr_pred_time, arr_pred_val)
        g1_projection.SetName(f"g1_projection_{mtype}")
        g1_projection.SetTitle("Projection (autoreg.)")
        g1_projection.SetFillStyle(0)
        g1_projection.SetLineColor(1)
        g1_projection.SetLineWidth(2)
        g1_projection.SetLineStyle(4)
        g1_projection.GetHistogram().SetOption("L")
        
        utils.root_plot1D(
            l_hist = [h1_dummy] + l_hists,
            l_graph_overlay = [
                #g1_projection,
                f1,
            ],
            outfile = f"{args.outdir}/progress_{mtype}.pdf",
            #xrange = (time_min, time_max),
            xrange = (time_start, time_end),
            #yrange = (0, 1.2 * max([_hist.GetMaximum() for _hist in l_hists])),
            yrange = (0, 1.5),
            logx = False,
            logy = False,
            xtitle = "Date",
            ytitle = f"Cumulative {mtype_label} fraction",
            timeformatx = "#lower[0.3]{#scale[0.9]{#splitline{%Y}{%b-%d}}}",
            gridx = True,
            gridy = True,
            ndivisionsx = (8, 1, 0),
            ndivisionsy = None,
            stackdrawopt = "nostack",
            legendpos = "UR",
            legendncol = 1,
            legendfillstyle = 0,
            legendfillcolor = 0,
            legendtextsize = 0.04,
            legendtitle = f"Latest data: {datetime.fromtimestamp(d_time_max[mtype]).strftime('%Y-%m-%d')}",
            legendheightscale = 0.9,
            legendwidthscale = 2.0,
            CMSextraText = "BTL Internal",
            lumiText = "Phase-2"
        )
        
    #print(d_module_info)
    
    
    return 0


if __name__ == "__main__" :
    
    main()