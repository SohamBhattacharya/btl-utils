#!/bin/bash

CAT_FILE="results/CIT/sm_summary/w-calib/SensorModule_categorization.yaml"
REWORKED_FILE="info/CIT/reworked_sms_new-barcodes_2026-08-24.txt"

for bc in $(yq .modules.R[] ${CAT_FILE}); do
    if ! grep -q $bc ${REWORKED_FILE}; then
        echo $bc
    fi
done


