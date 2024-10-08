#!/bin/bash

SRC=$1
DST=$2

# Transfer everything excluding (.hdf5, .h5) to destination
# and delete transferred files from the source

rsync \
    -asP \
    --remove-source-files \
    --exclude "*.hdf5" --exclude "*.hf5" \
    $SRC \
    $DST