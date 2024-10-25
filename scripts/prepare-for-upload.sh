#!/bin/bash

SRC=$1
DST=$2

# Transfer the .settings files
# Do not delete them from the source

rsync \
    -asP \
    --include "*.settings" --include "*/" --exclude "*" \
    $SRC \
    $DST

# Transfer everything excluding (*.settings, *.hdf5, *.h5) to destination
# and delete transferred files from the source

rsync \
    -asP \
    --remove-source-files \
    --exclude "*.settings" --exclude "*.hdf5" --exclude "*.hf5" \
    $SRC \
    $DST
