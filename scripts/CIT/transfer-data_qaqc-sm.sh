#!/bin/bash

set -eEu -x

SRC=~/mnt/cptlab_share/results/QAQC_SM/qaqc-gui_output/SM_QAQC_Production/
DST=/media/soham/D/Programs/Caltech/MTD/BTL/btl-production/data/QAQC_SM/qaqc-gui_output/SM_QAQC_Production/

RUNMIN=$1
RUNMAX=$2

RUNLIST=$(seq -f "run0%0.0f " $RUNMIN 1 $RUNMAX)

cd $SRC
msrsync3 -p 8 -P --stats --rsync "-as --exclude *.pdf" $(echo $RUNLIST) $DST/
