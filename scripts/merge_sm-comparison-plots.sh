#!/bin/bash

#set -x

BAC_DIRS=(
    CIT_MIB
    PKU_MIB
    UVA_MIB
    CIT_PKU
    CIT_UVA
    #MIB_PKU
    #MIB_UVA
    PKU_UVA
)

PLOT_NAMES=(
    g1_spe_L
    g1_spe_R
    g1_spe_bar
    
    g1_lo_L
    g1_lo_R
    g1_lo_bar
    
    g1_lo-asymmetry
    
    g1_src-charge_L
    g1_src-charge_R
    g1_src-charge_bar
    
    g1_peak-res_L
    g1_peak-res_R
    g1_peak-res_bar
)

INDIR=results/compare_sms/
OUTDIR=${INDIR}/merged_plots

mkdir -p $OUTDIR

for plt in ${PLOT_NAMES[@]}; do
    plt_paths=""
    for dir in ${BAC_DIRS[@]}; do
        plt_paths="${plt_paths} ${INDIR}/${dir}/${plt}_${dir}.png"
    
    done
    montage ${plt_paths} -tile 3x2 -geometry +0+0 -verbose ${OUTDIR}/${plt}_merged.png
done

#montage image1.png image2.png image3.png image4.png -tile 2x2 -geometry +0+0 output.png
