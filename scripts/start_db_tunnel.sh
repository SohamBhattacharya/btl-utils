#!/bin/bash

USER=$1

if [ -z "${USER}" ]; then
    echo "Error."
    echo "Usage: start_db_tunnel.sh <lxplus username>"
    exit 1
fi

ssh -f -N -L 8113:dbloader-mtd.cern.ch:8113 $USER@lxplus.cern.ch

