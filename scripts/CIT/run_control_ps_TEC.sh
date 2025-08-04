#!/bin/bash

set -eE

OPT=$1

if [ "$OPT" == "1" ]; then
    ./python/control_ps.py \
    --mode TEC \
    --pscfg configs/CIT/config_ps.yaml \
    --voltage 10 \
    --current 2.0
elif [ "$OPT" == "0" ]; then
    ./python/control_ps.py \
    --mode TEC \
    --pscfg configs/CIT/config_ps.yaml \
    --poff
else
    echo "Invalid usage."
    echo "Usage: run_control_ps_TEC <option>"
    echo "option: 1 to turn on the power supply, 0 to turn it off"
fi