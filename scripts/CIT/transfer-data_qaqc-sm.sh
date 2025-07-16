#!/bin/bash

set -eEu -x

RUNMIN="$1"
RUNMAX="$2"

SRC="$3"
DST="$4"

if [ -z "$SRC" ]; then
    SRC=~/mnt/cptlab_share/results/QAQC_SM/qaqc-gui_output/SM_QAQC_Production/
fi

if [ -z "$DST" ]; then
    DST=/media/soham/D/Programs/Caltech/MTD/BTL/btl-production/data/QAQC_SM/qaqc-gui_output/SM_QAQC_Production/
fi

#RUNLIST=$(seq -f "run0%0.0f " $RUNMIN 1 $RUNMAX)
#RUNLIST=()

declare -a RUNLIST=()

cd $SRC

for run in $(seq -f "run0%0.0f " $RUNMIN 1 $RUNMAX); do
    if [ -d "$run" ]; then
        RUNLIST+=("$run")
    fi
done

echo "${RUNLIST[@]}" 

msrsync3 -p 8 -P --stats --rsync "-as --exclude *.pdf" $(echo "${RUNLIST[@]}") $DST/
