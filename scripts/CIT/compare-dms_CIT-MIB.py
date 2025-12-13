#!/usr/bin/env python3

import os
import shutil
import glob
import math
import array
import sys
import time
import json

import numpy as np
import ROOT
import tdrstyle

from collections import OrderedDict
from typing import NamedTuple

#set the tdr style
tdrstyle.setTDRStyle()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetStatStyle(0)
ROOT.gStyle.SetOptFit(1111)
ROOT.gStyle.SetTitleOffset(1.25,'Y')
ROOT.gErrorIgnoreLevel = ROOT.kWarning;
ROOT.gROOT.SetBatch(True)
#ROOT.gROOT.SetBatch(False)


data_path ='/media/soham/D/Programs/Caltech/MTD/BTL/btl-production/data/dm-qaqc_cit-mib/data/'

fnames_MIB = glob.glob(data_path+'*.root')
fnames_CIT = glob.glob(data_path+'/dms-to-MIB_2025-10/*.root')

plotDir = 'results/'
modules = [ 32110040004376,
            32110040004575,
            32110040004580,
            32110040004581,
            32110040004585,
            32110040004588,
            32110040004602,
            32110040004640,
            32110040004648,
            32110040004731,
            32110040004748,
            32110040004765,
            32110040004795,
            32110040004829,
            32110040004836,
            32110040004940,
            32110040004979,
            32110040004993,
            32110040005007,
            32110040005045 ]

g_deltaT = ROOT.TGraph()
g_deltaTDiff = ROOT.TGraph()
g_deltaTDiff_vs_TambRatio = ROOT.TGraph()
g_deltaTDiff_vs_PowerRatio = ROOT.TGraph()

for module in modules:
    print(module)

    # select files to be compared that contain the module number
    fname_MIB = ''
    for fname in fnames_MIB:
        if str(module) in fname:
            fname_MIB = fname
    fname_CIT = ''
    for fname in fnames_CIT:
        if str(module) in fname:
            fname_CIT = fname
    print(fname_MIB, fname_CIT)

    # open MIB root file
    print(fname_MIB)
    f_MIB = ROOT.TFile.Open(fname_MIB)
    gDeltaTTopL_MIB = f_MIB.Get('g_DeltaTTopL')
    gDeltaTTopR_MIB = f_MIB.Get('g_DeltaTTopR')
    gDeltaTBottomL_MIB = f_MIB.Get('g_DeltaTBottomL')
    gDeltaTBottomR_MIB = f_MIB.Get('g_DeltaTBottomR')
    gCopperL_MIB = f_MIB.Get('g_TColdPlateL')
    gCopperR_MIB = f_MIB.Get('g_TColdPlateR')
    gPower_MIB = f_MIB.Get('g_power')

    # open CIT root file
    print(fname_CIT)
    f_CIT = ROOT.TFile.Open(fname_CIT)
    gDeltaTTopL_CIT = f_CIT.Get('g_DeltaTTopL')
    gDeltaTTopR_CIT = f_CIT.Get('g_DeltaTTopR')
    gDeltaTBottomL_CIT = f_CIT.Get('g_DeltaTBottomL')
    gDeltaTBottomR_CIT = f_CIT.Get('g_DeltaTBottomR')
    gCopperL_CIT = f_CIT.Get('g_CopperL')
    gCopperR_CIT = f_CIT.Get('g_CopperR')
    gPower_CIT = f_CIT.Get('g_power')

    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTTopL_MIB.Eval(4.), gDeltaTTopL_CIT.Eval(4.) )
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTTopR_MIB.Eval(4.), gDeltaTTopR_CIT.Eval(4.) )
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTBottomL_MIB.Eval(4.), gDeltaTBottomL_CIT.Eval(4.) )
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTBottomR_MIB.Eval(4.), gDeltaTBottomR_CIT.Eval(4.) )
    
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTTopL_CIT.Eval(4.), gDeltaTTopL_MIB.Eval(4.))
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTTopR_CIT.Eval(4.), gDeltaTTopR_MIB.Eval(4.))
    #g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTBottomL_CIT.Eval(4.), gDeltaTBottomL_MIB.Eval(4.))
    g_deltaT.SetPoint( g_deltaT.GetN(), gDeltaTBottomR_CIT.Eval(4.), gDeltaTBottomR_MIB.Eval(4.))

    #g_deltaTDiff.SetPoint( g_deltaTDiff.GetN(), gDeltaTTopL_MIB.Eval(4.), gDeltaTTopL_CIT.Eval(4.)- gDeltaTTopL_MIB.Eval(4.) )
    #g_deltaTDiff.SetPoint( g_deltaTDiff.GetN(), gDeltaTTopR_MIB.Eval(4.), gDeltaTTopR_CIT.Eval(4.)- gDeltaTTopR_MIB.Eval(4.) )
    #g_deltaTDiff.SetPoint( g_deltaTDiff.GetN(), gDeltaTBottomL_MIB.Eval(4.), gDeltaTBottomL_CIT.Eval(4.)-gDeltaTBottomL_MIB.Eval(4.) )
    g_deltaTDiff.SetPoint( g_deltaTDiff.GetN(), gDeltaTBottomR_MIB.Eval(4.), gDeltaTBottomR_CIT.Eval(4.)-gDeltaTBottomR_MIB.Eval(4.) )
    
    #g_deltaTDiff_vs_TambRatio.SetPoint( g_deltaTDiff_vs_TambRatio.GetN(), gCopperL_CIT.Eval(0.01)/gCopperL_MIB.Eval(0.01), (gDeltaTTopL_CIT.Eval(4.) - gDeltaTTopL_MIB.Eval(4.)) )
    #g_deltaTDiff_vs_TambRatio.SetPoint( g_deltaTDiff_vs_TambRatio.GetN(), gCopperL_CIT.Eval(0.01)/gCopperL_MIB.Eval(0.01), (gDeltaTTopR_CIT.Eval(4.) - gDeltaTTopR_MIB.Eval(4.)) )
    #g_deltaTDiff_vs_TambRatio.SetPoint( g_deltaTDiff_vs_TambRatio.GetN(), gCopperL_CIT.Eval(0.01)/gCopperL_MIB.Eval(0.01), (gDeltaTBottomL_CIT.Eval(4.) - gDeltaTBottomL_MIB.Eval(4.)) )
    g_deltaTDiff_vs_TambRatio.SetPoint( g_deltaTDiff_vs_TambRatio.GetN(), gCopperL_CIT.Eval(0.01)/gCopperL_MIB.Eval(0.01), (gDeltaTBottomR_CIT.Eval(4.) - gDeltaTBottomR_MIB.Eval(4.)) )
    
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.)/gPower_MIB.Eval(4.), (gDeltaTTopL_CIT.Eval(4.) - gDeltaTTopL_MIB.Eval(4.)) )
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.)/gPower_MIB.Eval(4.), (gDeltaTTopR_CIT.Eval(4.) - gDeltaTTopR_MIB.Eval(4.)) )
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.)/gPower_MIB.Eval(4.), (gDeltaTBottomL_CIT.Eval(4.) - gDeltaTBottomL_MIB.Eval(4.)) )
    g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.)/gPower_MIB.Eval(4.), (gDeltaTBottomR_CIT.Eval(4.) - gDeltaTBottomR_MIB.Eval(4.)) )
    
    #dt = gDeltaTBottomR_CIT.Eval(4.)
    #dt_corr = -4.549 + (0.7667 * dt)
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.)/gPower_MIB.Eval(4.), (dt_corr - gDeltaTBottomR_MIB.Eval(4.)) )
    
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_CIT.Eval(4.), (gDeltaTBottomR_CIT.Eval(4.) - gDeltaTBottomR_MIB.Eval(4.)) )
    #g_deltaTDiff_vs_PowerRatio.SetPoint( g_deltaTDiff_vs_PowerRatio.GetN(), gPower_MIB.Eval(4.), (gDeltaTBottomR_CIT.Eval(4.) - gDeltaTBottomR_MIB.Eval(4.)) )

ROOT.gStyle.SetOptStat(1110) 

c = ROOT.TCanvas('c_DeltaT','', 800, 700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hPad = ROOT.gPad.DrawFrame( -20., -20., -15., -15. )
#hPad.SetTitle(';#DeltaT [C] - MIB;#DeltaT [C] - CIT')
hPad.SetTitle(';#DeltaT [C] - CIT;#DeltaT [C] - MIB')
hPad.Draw()
g_deltaT.SetMarkerStyle(20)
g_deltaT.SetMarkerColor(ROOT.kBlack)
g_deltaT.SetLineColor(ROOT.kBlack)
g_deltaT.Draw('P,same')
TF1_diag = ROOT.TF1('diag','x',-30.,0.)
TF1_diag.SetLineColor(ROOT.kBlack)
TF1_diag.SetLineStyle(1)
TF1_diag.SetLineWidth(1)
TF1_diag.Draw('same')
TF1_fit = ROOT.TF1('fit','pol1',-30.,0.)
#g_deltaT.Fit('fit','QNRS+')
g_deltaT.Fit('fit','QRS+')
TF1_fit.SetLineColor(ROOT.kRed)
TF1_fit.SetLineStyle(2)
TF1_fit.SetLineWidth(2)
TF1_fit.Draw('same')
c.Print(plotDir+'DeltaT.png')

c = ROOT.TCanvas('c_DeltaTDiff','', 800, 700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hPad = ROOT.gPad.DrawFrame( -20., -2., -17., 2. )
hPad.SetTitle(';#DeltaT [C] - MIB;#Delta(#DeltaT)_{CIT-MIB} [C]')
hPad.Draw()
g_deltaTDiff.SetMarkerStyle(20)
g_deltaTDiff.SetMarkerColor(ROOT.kBlack)
g_deltaTDiff.SetLineColor(ROOT.kBlack)
g_deltaTDiff.Draw('P,same')
TF1_fitDiff = ROOT.TF1('fitDiff','pol1',-30.,0.)
g_deltaTDiff.Fit('fitDiff','NRS+')
TF1_fitDiff.SetLineColor(ROOT.kRed)
TF1_fitDiff.SetLineStyle(2)
TF1_fitDiff.SetLineWidth(2)
TF1_fitDiff.Draw('same')
c.Print(plotDir+'DeltaTDiff.png')

c = ROOT.TCanvas('c_DeltaTDiff_vs_TambRatio','', 800, 700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hPad = ROOT.gPad.DrawFrame( 0.8, -2., 1.2, 2. )
hPad.SetTitle(';T_{amb} ratio CIT / MIB;#Delta(#DeltaT)_{CIT-MIB} [C]')
hPad.Draw()
g_deltaTDiff_vs_TambRatio.SetMarkerStyle(20)
g_deltaTDiff_vs_TambRatio.SetMarkerColor(ROOT.kBlack)
g_deltaTDiff_vs_TambRatio.SetLineColor(ROOT.kBlack)
g_deltaTDiff_vs_TambRatio.Draw('P,same')
TF1_fit = ROOT.TF1(f'fit_{c.GetName()}','pol0',0.8, 1.2)
g_deltaTDiff_vs_TambRatio.Fit(TF1_fit.GetName(),'RSMEF+')
TF1_fit.SetLineColor(ROOT.kRed)
TF1_fit.SetLineStyle(2)
TF1_fit.SetLineWidth(2)
TF1_fit.Draw('same')
c.Print(plotDir+'DeltaTDiff_vs_TambRatio.png')

c = ROOT.TCanvas('c_DeltaTDiff_vs_PowerRatio','', 800, 700)
ROOT.gPad.SetGridx()
ROOT.gPad.SetGridy()
hPad = ROOT.gPad.DrawFrame( 0.8, -2., 1.2, 2. )
hPad.SetTitle(';Power ratio CIT / MIB;#Delta(#DeltaT)_{CIT-MIB} [C]')
hPad.Draw()
g_deltaTDiff_vs_PowerRatio.SetMarkerStyle(20)
g_deltaTDiff_vs_PowerRatio.SetMarkerColor(ROOT.kBlack)
g_deltaTDiff_vs_PowerRatio.SetLineColor(ROOT.kBlack)
g_deltaTDiff_vs_PowerRatio.Draw('P,same')
TF1_fit = ROOT.TF1(f'fit_{c.GetName()}','pol0',0.8, 1.2)
g_deltaTDiff_vs_PowerRatio.Fit(TF1_fit.GetName(),'RSMEF+')
TF1_fit.SetLineColor(ROOT.kRed)
TF1_fit.SetLineStyle(2)
TF1_fit.SetLineWidth(2)
TF1_fit.Draw('same')
c.Print(plotDir+'DeltaTDiff_vs_PowerRatio.png')
print(np.mean(g_deltaTDiff_vs_PowerRatio.GetX()))
print(np.mean(g_deltaTDiff_vs_PowerRatio.GetY()))
