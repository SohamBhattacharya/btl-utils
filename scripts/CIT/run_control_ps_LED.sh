#!/bin/bash

set -eE

OPT=$1

if [ "$OPT" == "1" ]; then
    ./python/control_ps.py \
    --mode LED \
    --pscfg configs/CIT/config_ps.yaml \
    --voltage 12 \
    --current 0.1 \
    --channels 2
elif [ "$OPT" == "0" ]; then
    ./python/control_ps.py \
    --mode LED \
    --pscfg configs/CIT/config_ps.yaml \
    --poff
else
    echo "Invalid usage."
    echo "Usage: $0 <option>"
    echo "option: 1 to turn on the power supply, 0 to turn it off"
fi
