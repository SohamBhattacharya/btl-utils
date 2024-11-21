import argparse
import dataclasses
import itertools
import json
import os
import re
import subprocess
import tqdm
import yaml

import ROOT
ROOT.gROOT.SetBatch(1)

import cms_lumi as cms_lumi


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
): pass


@dataclasses.dataclass(init = True)
class DetectorModule :
    
    barcode: str = None
    id: str = None
    feb: str = None
    sm1: str = None
    sm2: str = None
    
    def dict(self) :
        
        return dataclasses.asdict(self)


class DictClass:
     
    def __init__(self, dict):
        self.__dict__.update(dict)


def dict_to_obj(dict):
     
    return json.loads(json.dumps(dict), object_hook = DictClass)

def run_cmd_list(l_cmd, debug = False) :
    
    for cmd in l_cmd :
        
        if (debug) :
            
            print(f"Trying command: {cmd}")
        
        retval = os.system(cmd)
        
        if (retval) :
            
            exit()


def natural_sort(l):
    
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)


def parse_string_regex(
    s,
    regexp
) :
    
    rgx = re.compile(regexp)
    result = [m.groupdict() for m in rgx.finditer(s)][0]
    
    return result


def get_part_id(barcode) :
    """
    Get part ID for given barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}'"
    ], stdout = subprocess.PIPE)
    
    id = dbquery_output.stdout.decode("utf-8").split()[1].strip()
    
    return id


def get_dm_barcodes(location_id = None) :
    """
    Get list of DM barcodes
    Caltech location: 5023
    """
    
    query = "select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'DetectorModule'"
    
    if (location_id is not None) :
        
        query = f"{query} AND s.LOCATION_ID = {location_id}"
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        query
    ], stdout = subprocess.PIPE)
    
    l_dm_barcode = dbquery_output.stdout.decode("utf-8").split()[1:]
    l_dm_barcode = [_barcode.strip() for _barcode in l_dm_barcode]
    
    return l_dm_barcode


def get_dm_sm_barcodes(barcode) :
    """
    Get list of SM barcodes for a given DM barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'SensorModule' AND s.PART_PARENT_ID = (select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}')"
    ], stdout = subprocess.PIPE)
    
    l_sm_barcode = dbquery_output.stdout.decode("utf-8").split()[1:]
    l_sm_barcode = [_barcode.strip() for _barcode in l_sm_barcode]
    
    return l_sm_barcode


def get_dm_feb_barcode(barcode) :
    """
    Get FEB barcode for a given DM barcode
    """
    
    dbquery_output = subprocess.run([
        "./scripts/rhapi.py",
        "-u", "http://localhost:8113",
        f"select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = 'FE' AND s.PART_PARENT_ID = (select s.ID from mtd_cmsr.parts s where s.BARCODE = '{barcode}')"
    ], stdout = subprocess.PIPE)
    
    feb_barcode = dbquery_output.stdout.decode("utf-8").split()[1].strip()
    
    return feb_barcode


def get_used_sm_barcodes(location_id = None, yamlfile = None, d_dms = None) :
    """
    Get list of all used (assembled into DMs) SM barcodes
    If yamlfile is provided, will load existing information from there
    If fetch additional DM info from the database if they are not in the file
    """
    
    # Show all columns:
    # ./rhapi.py -u http://localhost:8113 "select s.* from mtd_cmsr.parts s where s.KIND_OF_PART = 'DetectorModule'"
    
    d_dms = get_all_dm_info(
        yamlfile = yamlfile,
        location_id = location_id,
    )
    
    l_sm_barcodes = list(itertools.chain(*[[_dm.sm1, _dm.sm2] for _dm in d_dms.values()]))
    
    return l_sm_barcodes


def get_dm_info(barcode) :
    """
    Get DM information
    """
    
    id = get_part_id(barcode)
    feb = get_dm_feb_barcode(barcode)
    l_sms = sorted(get_dm_sm_barcodes(barcode))
    
    dm = DetectorModule(
        id = id,
        barcode = barcode,
        feb = feb,
        sm1 = l_sms[0],
        sm2 = l_sms[1],
    )
    
    return dm


def get_all_dm_info(location_id = None, yamlfile = None) :
    """
    Get the information for all DMs
    If yamlfile is provided, will load the information from there
    Will fetch the information of addtional DMs from the database if they are not in the file
    """
    
    l_dm_barcode = get_dm_barcodes(location_id = location_id)
    
    d_dms = load_dm_info(yamlfile) if yamlfile else {}
    
    print("Fetching DM information from the database ... ")
    
    for barcode in tqdm.tqdm(l_dm_barcode) :
        
        if barcode in d_dms :
            
            continue
            
        d_dms[barcode] = get_dm_info(barcode)#.dict()
    
    print(f"Fetched information for {len(d_dms)} from the database.")
    
    return d_dms


def load_dm_info(yamlfile) :
    """
    Load DM info from yamlfile
    """
    
    d_dms = {}
    
    if (os.path.exists(yamlfile)) :
        
        print(f"Loading DM information from file: ({yamlfile}) ...")
        
        with open(yamlfile, "r") as fopen :
            
            d_dms = yaml.load(fopen.read(), Loader = yaml.FullLoader)
        
        # Convert dict to DetectorModule object
        d_dms = {_key: DetectorModule(**_val) for _key, _val in d_dms.items()}
        
        print(f"Loaded information for {len(d_dms)} DMs.")
    
    else :
        
        print(f"DM information file ({yamlfile}) does not exist. No DM information loaded.")
    
    return d_dms


def save_all_dm_info(outyamlfile, inyamlfile = None, location_id = None, ret = False) :
    """
    Load existing DM info from inyamlfile
    Fetch additional DM info from database
    Save all DM info into outyamlfile
    """
    
    d_dms_orig = get_all_dm_info(yamlfile = inyamlfile, location_id = location_id)
    
    # Convert DetectorModule object to dict
    d_dms = {_key: _val.dict() for _key, _val in d_dms_orig.items()}
    
    outdir = os.path.dirname(outyamlfile)
    
    if len(outdir) :
        
        os.system(f"mkdir -p {outdir}")
    
    print(f"Saving DM information to file: {outyamlfile} ...")
    
    with open(outyamlfile, "w") as fopen :
        
        fopen.write(yaml.dump(d_dms))
    
    print(f"Saved information for {len(d_dms)} DMs.")
    
    if ret :
        
        return d_dms_orig


def handle_flows(hist, underflow = True, overflow = True) :
    
    nbins = hist.GetNbinsX()
    
    if (underflow) :
        
        hist.AddBinContent(1, hist.GetBinContent(0))
        hist.SetBinContent(0, 0.0)
        hist.SetBinError(0, 0.0)
    
    if (overflow) :
        
        hist.AddBinContent(nbins, hist.GetBinContent(nbins+1))
        hist.SetBinContent(nbins+1, 0.0)
        hist.SetBinError(nbins+1, 0.0)


def get_canvas(ratio = False) :
    
    ROOT.gROOT.LoadMacro(os.path.split(os.path.realpath(__file__))[0]+"/tdrstyle.C")
    ROOT.gROOT.ProcessLine("setTDRStyle();")
    
    ROOT.gROOT.SetStyle("tdrStyle")
    ROOT.gROOT.ForceStyle(True)
    
    ROOT.gStyle.SetPadTickX(0)
    ROOT.gStyle.SetHatchesSpacing(7*ROOT.gStyle.GetHatchesSpacing())
    ROOT.gStyle.SetHatchesLineWidth(1)
    
    canvas = ROOT.TCanvas("canvas", "canvas", 1600, 1300)
    canvas.UseCurrentStyle()
    
    
    if (ratio) :
        
        canvas.Divide(1, 2)
        
        canvas.cd(1).SetPad(0, 0.32, 1, 1)
        canvas.cd(1).SetTopMargin(0.075)
        canvas.cd(1).SetBottomMargin(0)
        
        canvas.cd(2).SetPad(0, 0.0, 1, 0.3)
        canvas.cd(2).SetTopMargin(0.05)
        canvas.cd(2).SetBottomMargin(0.285)
        
        canvas.cd(2).SetLeftMargin(0.125)
        canvas.cd(2).SetRightMargin(0.05)
    
    else :
        
        #canvas.SetLeftMargin(0.16)
        #canvas.SetRightMargin(0.05)
        canvas.SetTopMargin(0.05)
        #canvas.SetBottomMargin(0.135)
        canvas.SetLeftMargin(0.125)
        canvas.SetRightMargin(0.05)

    
    return canvas


def root_plot1D(
    l_hist,
    outfile,
    xrange,
    yrange,
    ratio_num_den_pairs = [],
    l_hist_overlay = [],
    l_graph_overlay = [],
    gr_overlay_drawopt = "PE1",
    ratio_mode = "mc",
    no_xerror = False,
    logx = False,
    logy = False,
    title = "",
    xtitle = "",
    ytitle = "",
    xtitle_ratio = "",
    ytitle_ratio = "",
    yrange_ratio = (0, 2),
    centertitlex = True,
    centertitley = True,
    centerlabelx = False,
    centerlabely = False,
    gridx = False, gridy = False,
    ndivisionsx = None,
    ndivisionsy = None,
    ndivisionsy_ratio = (5, 5, 0),
    stackdrawopt = "nostack",
    ratiodrawopt = "hist",
    legendpos = "UR",
    legendncol = 1,
    legendfillstyle = 0,
    legendfillcolor = 0,
    legendtextsize = 0.045,
    legendtitle = "",
    legendheightscale = 1.0,
    legendwidthscale = 1.0,
    CMSextraText = "Internal",
    lumiText = "Phase-2"
    ) :
    
    canvas = get_canvas(ratio = len(ratio_num_den_pairs))
    
    if (no_xerror) :
        
        ROOT.gStyle.SetErrorX(not no_xerror)
    
    canvas.cd(1)
    
    legendHeight = legendheightscale * 0.065 * (len(l_hist) + 1.5*(len(legendtitle)>0))
    legendWidth = legendwidthscale * 0.4
    
    padTop = 1 - 0.3*canvas.GetTopMargin() - ROOT.gStyle.GetTickLength("y")
    padRight = 1 - canvas.GetRightMargin() - 0.6*ROOT.gStyle.GetTickLength("x")
    padBottom = canvas.GetBottomMargin() + 0.6*ROOT.gStyle.GetTickLength("y")
    padLeft = canvas.GetLeftMargin() + 0.6*ROOT.gStyle.GetTickLength("x")
    
    if(legendpos == "UR") :
        
        legend = ROOT.TLegend(padRight-legendWidth, padTop-legendHeight, padRight, padTop)
    
    elif(legendpos == "LR") :
        
        legend = ROOT.TLegend(padRight-legendWidth, padBottom, padRight, padBottom+legendHeight)
    
    elif(legendpos == "LL") :
        
        legend = ROOT.TLegend(padLeft, padBottom, padLeft+legendWidth, padBottom+legendHeight)
    
    elif(legendpos == "UL") :
        
        legend = ROOT.TLegend(padLeft, padTop-legendHeight, padLeft+legendWidth, padTop)
    
    else :
        
        print("Wrong legend position option:", legendpos)
        exit(1)
    
    
    legend.SetNColumns(legendncol)
    legend.SetFillStyle(legendfillstyle)
    legend.SetFillColor(legendfillcolor)
    legend.SetBorderSize(0)
    legend.SetHeader(legendtitle)
    legend.SetTextSize(legendtextsize)
    
    stack = ROOT.THStack()
    
    for hist in l_hist :
        
        hist.GetXaxis().SetRangeUser(xrange[0], xrange[1])
        #hist.SetFillStyle(0)
        
        #stack.Add(hist, "hist")
        stack.Add(hist, hist.GetOption())
        
        if (len(hist.GetTitle())) :
            
            legend.AddEntry(hist, hist.GetTitle(), "F")#, "LP")
    
    # Add a dummy histogram so that the X-axis range can be beyond the histogram range
    #h1_xRange = ROOT.TH1F("h1_xRange", "h1_xRange", 1, xrange[0], xrange[1])
    #stack.Add(h1_xRange)
    
    stack.Draw(stackdrawopt)
    
    stack.GetXaxis().SetRangeUser(xrange[0], xrange[1])
    stack.SetMinimum(yrange[0])
    stack.SetMaximum(yrange[1])
    
    if (len(l_hist_overlay)) :
        
        stack_overlay = ROOT.THStack()
        stack_overlay.SetName("stack_overlay")
        
        for hist in l_hist_overlay :
            
            #hist.Draw(f"same {hist.GetOption()}")
            #print(hist.GetOption())
            #print(hist.GetLineWidth())
            #print(hist.GetMarkerSize())
            #print(hist.GetMarkerStyle())
            stack_overlay.Add(hist, hist.GetOption())
            
            if (len(hist.GetTitle())) :
                
                legend.AddEntry(hist, hist.GetTitle())#, hist.GetOption())#, "LPE")
        
        stack_overlay.Draw("nostack same")
        
        stack_overlay.GetXaxis().SetRangeUser(xrange[0], xrange[1])
        stack_overlay.SetMinimum(yrange[0])
        stack_overlay.SetMaximum(yrange[1])
    
    if (ndivisionsx is not None) :
        
        stack.GetXaxis().SetNdivisions(ndivisionsx[0], ndivisionsx[1], ndivisionsx[2], False)
    
    if (ndivisionsy is not None) :
        
        stack.GetYaxis().SetNdivisions(ndivisionsy[0], ndivisionsy[1], ndivisionsy[2], False)
    
    stack.GetXaxis().SetTitle(xtitle)
    #stack.GetXaxis().SetTitleSize(ROOT.gStyle.GetTitleSize("X") * xTitleSizeScale)
    #stack.GetXaxis().SetTitleOffset(ROOT.gStyle.GetTitleOffset("X") * 1.1)
    
    stack.GetYaxis().SetTitle(ytitle)
    stack.GetYaxis().SetTitleSize(0.055)
    #print(stack.GetYaxis().GetTitleSize())
    #stack.GetYaxis().SetTitleSize(ROOT.gStyle.GetTitleSize("Y") * yTitleSizeScale)
    stack.GetYaxis().SetTitleOffset(1)
    
    #stack.SetTitle(title)

    stack.GetXaxis().CenterTitle(centertitlex)
    stack.GetYaxis().CenterTitle(centertitley)
    
    stack.GetXaxis().CenterLabels(centerlabelx)
    stack.GetYaxis().CenterLabels(centerlabely)
    
    for gr in l_graph_overlay :
            
            legend.AddEntry(gr, gr.GetTitle())
            gr.Draw(gr_overlay_drawopt)
    
    legend.Draw()
    
    canvas.cd(1).SetLogx(logx)
    canvas.cd(1).SetLogy(logy)
    
    canvas.cd(1).SetGridx(gridx)
    canvas.cd(1).SetGridy(gridy)
    
    cms_lumi.lumiTextSize = 0.99
    cms_lumi.cmsTextSize = 0.99
    cms_lumi.relPosX = 0.045
    cms_lumi.CMS_lumi(pad = canvas.cd(1), iPeriod = 0, iPosX = 0, CMSextraText = CMSextraText, lumiText = lumiText)
    
    
    if (len(ratio_num_den_pairs)) :
        
        canvas.cd(2)
        
        stack_ratio = ROOT.THStack()
        
        l_gr_ratio_err = []
        
        for h1_num, h1_den in ratio_num_den_pairs :
            
            h1_ratio = h1_num.Clone()
            h1_ratio.GetXaxis().SetRangeUser(xrange[0], xrange[1])
            
            h1_ratio.Divide(h1_den)
            
            if (ratio_mode == "default") :
                
                pass
            
            elif (ratio_mode == "data") :
                
                gr_ratio_err = ROOT.TGraphAsymmErrors(h1_ratio.GetNbinsX())
                
                for ibin in range(0, h1_ratio.GetNbinsX()) :
                    
                    gr_ratio_err.SetPoint(ibin, h1_ratio.GetBinCenter(ibin+1), 1.0)
                    
                    if (h1_num.GetBinContent(ibin+1)) :
                        
                        print(h1_num.GetBinError(ibin+1), h1_num.GetBinContent(ibin+1), h1_num.GetBinError(ibin+1) / h1_num.GetBinContent(ibin+1))
                        h1_ratio.SetBinError(ibin+1, h1_ratio.GetBinContent(ibin+1) * h1_num.GetBinError(ibin+1) / h1_num.GetBinContent(ibin+1))
                    
                    if (h1_den.GetBinContent(ibin+1)) :
                        
                        ratio_err_upr = h1_den.GetBinError(ibin+1)/h1_den.GetBinContent(ibin+1)
                        ratio_err_lwr = h1_den.GetBinError(ibin+1)/h1_den.GetBinContent(ibin+1)
                        
                        gr_ratio_err.SetPointEYhigh(ibin, ratio_err_upr)
                        gr_ratio_err.SetPointEYlow(ibin, ratio_err_lwr)
                    
                    gr_ratio_err.SetPointEXhigh(ibin, h1_ratio.GetBinWidth(ibin+1) / 2.0)
                    gr_ratio_err.SetPointEXlow(ibin, h1_ratio.GetBinWidth(ibin+1) / 2.0)
                    
                    gr_ratio_err.SetFillColorAlpha(1, 1.0)
                    gr_ratio_err.SetFillStyle(3354)
                    gr_ratio_err.SetMarkerSize(0)
                    gr_ratio_err.SetLineWidth(0)
                
                #legend.AddEntry(gr_ratio_err, "error", "f")
                l_gr_ratio_err.append(gr_ratio_err)
            
            stack_ratio.Add(h1_ratio, ratiodrawopt)
        
        
        stack_ratio.Draw("nostack")
        
        stack_ratio.GetXaxis().SetRangeUser(xrange[0], xrange[1])
        stack_ratio.SetMinimum(yrange_ratio[0])
        stack_ratio.SetMaximum(yrange_ratio[1])
        
        if (ndivisionsx is not None) :
            
            stack_ratio.GetXaxis().SetNdivisions(ndivisionsx[0], ndivisionsx[1], ndivisionsx[2], False)
        
        if (ndivisionsy_ratio is not None) :
            
            stack_ratio.GetYaxis().SetNdivisions(ndivisionsy_ratio[0], ndivisionsy_ratio[1], ndivisionsy_ratio[2], False)
        
        stack_ratio.GetXaxis().CenterLabels(centerlabelx)
        stack_ratio.GetYaxis().CenterLabels(centerlabely)
        
        stack_ratio.GetXaxis().SetLabelSize(0.1)
        stack_ratio.GetYaxis().SetLabelSize(0.1)
        
        stack_ratio.GetXaxis().SetTitle(xtitle_ratio)
        stack_ratio.GetXaxis().SetTitleSize(0.13)
        stack_ratio.GetXaxis().SetTitleOffset(0.91)
        stack_ratio.GetXaxis().CenterTitle(centertitlex)
        
        stack_ratio.GetYaxis().SetTitle(ytitle_ratio)
        stack_ratio.GetYaxis().SetTitleSize(0.115)
        stack_ratio.GetYaxis().SetTitleOffset(0.45)
        stack_ratio.GetYaxis().CenterTitle(centertitley)
        
        for gr in l_gr_ratio_err :
            
            gr.Draw("E2")
        
        canvas.cd(2).SetGridx(gridx)
        canvas.cd(2).SetGridy(gridy)
    
    outdir = os.path.dirname(outfile)
    outfile_noext = os.path.splitext(outfile)[0]
    
    if (len(outdir)) :
        
        os.system(f"mkdir -p {outdir}")
    
    canvas.SaveAs(f"{outfile_noext}.pdf")
    canvas.SaveAs(f"{outfile_noext}.png")
    canvas.Close()
    
    return 0