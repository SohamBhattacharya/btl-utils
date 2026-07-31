#!/bin/bash

set -x

FNAMES=(
    g1_deltaTcorr-avg_vs_refT.png
    g1_deltaT-avg_vs_deltaT-offset.png
    g1_deltaT-avg_vs_power.png
    g1_deltaT-avg_vs_refT.png
    g1_deltaT-avg_vs_refT-tec.png
    g1_deltaT-avg_vs_ref-deltaT.png
    g1_deltaT-avg_vs_tec-sum.png
    g1_deltaT-std_vs_barcode.png
    g1_deltaT-std_vs_deltaT-avg.png
    g1_deltaT-std_vs_tec-std.png
    g1_deltaT_vs_barcode.png
    g1_power_vs_tec-sum.png
    g1_refT_vs_barcode.png
    g1_tec-sum-bac_vs_barcode.png
    g1_tec-sum-bac_vs_tec-sum.png
    g1_tec-sum_vs_barcode.png
    h1_deltaTcorr_4min.png
    h1_deltaT-std_4min.png
    h1_deltaT_4min.png
)

INDIR=/home/soham/mnt/eos_mtd_www/BTL/production/BAC_results/module_summaries
#INDIR=tmp/BAC_results/module_summaries
OUTDIR=results/ALL/dm_summary

mkdir -p $OUTDIR

for fname in ${FNAMES[@]}; do
    convert \
    $INDIR/CIT/dm_summary/$fname \
    $INDIR/MIB/dm_summary/$fname \
    $INDIR/PKU/dm_summary/$fname \
    $INDIR/UVA/dm_summary/$fname \
    +append $OUTDIR/$fname
done
