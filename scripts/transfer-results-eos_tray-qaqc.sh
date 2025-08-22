#!/bin/bash

set -eEu

FNAME="$1" # File to transfer
USER="$2" # lxplus username
LOC="$3" # CIT | CERN | MIB | PKU | UVA

FNAME_BASE=$(basename "$FNAME")

EOS_PATH="/eos/user/m/mtd/www/BTL/production/BAC_results/tray_qaqc/${LOC}/"

rsync -asP -e "ssh -o ControlMaster=no -o ControlPath=~/.ssh/control:%C" "$FNAME" ${USER}@lxplus.cern.ch:${EOS_PATH}/

ssh \
-o ControlMaster=no \
-o ControlPath=~/.ssh/control:%C sobhatta@lxplus.cern.ch \
-f "pushd ${EOS_PATH} && tar -xv -f ${FNAME_BASE} && popd"