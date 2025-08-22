#!/bin/bash

#set -eEx

USER="$1"
OPT="$2"

SRC=${USER}@lxplus.cern.ch:/eos/user/m/mtd/www
MPOINT=${HOME}/mnt/eos_mtd_www

mountpoint -q $MPOINT
ISMOUNTED=$?

if [ -n "${USER}" ] && [ "$OPT" = "1" ]; then
    if [ $ISMOUNTED -eq 0 ]; then
        echo "$MPOINT already a mountpoint. Unmount and try again."
    else
        echo "Mounting..."
        
        mkdir -p $MPOINT
        sshfs $SRC $MPOINT -o ServerAliveInterval=60 -o TCPKeepAlive=yes -o auto_cache,reconnect,no_readahead -o compression=no
        
        mountpoint -q $MPOINT
        ISMOUNTED=$?
        
        if [ $ISMOUNTED -eq 0 ]; then
            echo "Mounted successfully."
        else
            echo "Mounting failed."
        fi
    fi
elif [ -n "${USER}" ] && [ "$OPT" = "0" ]; then
    echo "Unmounting..."
    fusermount -u $MPOINT
    
    mountpoint -q $MPOINT
    ISMOUNTED=$?
    
    if [ $ISMOUNTED -ne 0 ]; then
        echo "Unmounted successfully."
    else
        echo "Unmounting failed."
    fi
else
    echo "Usage: "$(basename "$0")" <lxplus username> <OPT>"
    echo "    <OPT> = 1/0 for mount/unmount"
fi
