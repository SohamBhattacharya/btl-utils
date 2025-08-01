#!/bin/bash

set -eE

OPT=$1

if [ "$OPT" == "1" ]; then
    ./python/control_ps.py \
    --mode HV \
    --pscfg configs/CIT/config_ps.yaml \
    --voltage 45 \
    --current 1.0
elif [ "$OPT" == "0" ]; then
    ./python/control_ps.py \
    --mode HV \
    --pscfg configs/CIT/config_ps.yaml \
    --poff
else
    echo "Invalid usage."
    echo "Usage: run_control_ps_HV <option>"
    echo "option: 1 to turn on the power supply, 0 to turn it off"
fi