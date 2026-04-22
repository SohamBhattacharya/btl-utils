#!/bin/bash

RU_INFO=$1
TRAY_START=$2

if [ -z "$RU_INFO" ] || [ -z "$TRAY_START" ]; then
    echo "Usage: $0 <RU_INFO> <TRAY_START>"
    exit 1
fi

RUS=( $(yq .[].barcode "$RU_INFO" | sort -k1.12) )

#echo ${RUS[@]}

NRUS=${#RUS[@]}
TRAY=$TRAY_START
NRUS_PER_TRAY=6

echo "Found $NRUS RUs. Grouping into trays..."

for ((i=0; i < NRUS; i += NRUS_PER_TRAY)); do
    tray_rus=("${RUS[@]:i:NRUS_PER_TRAY}")
    
    echo "Tray $TRAY RUs:"
    
    for ru in "${tray_rus[@]}"; do
        echo "  $ru"
    done
    
    ((TRAY++))
done