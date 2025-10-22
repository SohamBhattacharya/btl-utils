#!/bin/bash

DIR=~/mnt/cptlab_share/results/QAQC_tray/runs/tofhir/run_822
FILE=$(find $DIR/temperatures_*.json | sort -V | tail -n 1)

echo $FILE

COMPONENTS=(
    DM03
    CCBOARD
    PCCA
    PCCB
)

for CMP in "${COMPONENTS[@]}"; do
    echo $CMP
    jq ".${CMP}" $FILE
done
