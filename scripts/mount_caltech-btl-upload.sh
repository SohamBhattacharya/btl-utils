#!/bin/bash

OPT=$1

SRC="btl-upload@login-2.ultralight.org:/"
MPOINT="/home/cptlab/mnt/btl-upload"
mkdir -p $MPOINT

mountpoint -q $MPOINT
ISMOUNTED=$?

if [ "$OPT" = "1" ]; then
    if [ $ISMOUNTED -eq 0 ]; then
        echo "$MPOINT already a mountpoint. Unmount and try again."
    else
        echo "Mounting..."
        sshfs $SRC $MPOINT -o ServerAliveInterval=60 -o TCPKeepAlive=yes
        
        mountpoint -q $MPOINT
        ISMOUNTED=$?
        
        if [ $ISMOUNTED -eq 0 ]; then
            echo "Mounted successfully."
        else
            echo "Mounting failed."
        fi
    fi
elif [ "$OPT" = "0" ]; then
    
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
    echo "Usage: "$(basename "$0")" <OPT>"
    echo "    <OPT> = 1/0 for mount/unmount"
fi
