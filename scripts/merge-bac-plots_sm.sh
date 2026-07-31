#!/bin/bash

set -x

FNAMES=(
    g1_cat_vs_barcode.png
    g1_lo-avg_vs_barcode.png
    g1_lo-max_vs_barcode.png
    g1_lo-min_vs_barcode.png
    g1_metrics_vs_barcode.png
    g1_peak-res-avg_vs_barcode.png
    g1_peak-res-max_vs_barcode.png
    g1_peak-res-max_vs_lyso.png
    g1_spe-avg_vs_barcode.png
    g1_spe-max_vs_barcode.png
    g1_spe-min_vs_barcode.png
    g1_src-chg-avg_vs_barcode.png
    h1_lo-asymm_LR_bar.png
    h1_lo-asymm_avg_bar.png
    h1_lo-avg_bar.png
    h1_lo_LR_bar.png
    h1_lo_fom_bar.png
    h1_metric_barcodes.png
    h1_metric_counts.png
    h1_peak-res-avg_bar.png
    h1_peak-res_LR_bar.png
    h1_spe_LR_bar.png
    h1_src-chg_LR_bar.png
)

INDIR=/home/soham/mnt/eos_mtd_www/BTL/production/BAC_results/module_summaries
#INDIR=tmp/BAC_results/module_summaries
OUTDIR=results/ALL/sm_summary

mkdir -p $OUTDIR

for fname in ${FNAMES[@]}; do
    convert \
    $INDIR/CIT/sm_summary/$fname \
    $INDIR/MIB/sm_summary/$fname \
    $INDIR/PKU/sm_summary/$fname \
    $INDIR/UVA/sm_summary/$fname \
    +append $OUTDIR/$fname
done
