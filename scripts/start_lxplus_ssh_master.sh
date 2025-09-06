#!/bin/bash

set -eE

USER=$1
OPT=$2

if [ "$OPT" = "1" ]; then
    ssh -nNf -M -Y -o ServerAliveInterval=60 -o TCPKeepAlive=yes -o ControlPath=~/.ssh/control:%C $USER@lxplus.cern.ch
elif [ "$OPT" = "0" ]; then
    ssh -O exit -o ControlPath=~/.ssh/control:%C $USER@lxplus.cern.ch
else
    echo "Usage: "$(basename "$0")" <lxplus username> <OPT>"
    echo "    <OPT> = 1/0 for open/close"
fi