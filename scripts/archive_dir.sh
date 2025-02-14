#!/bin/bash

DIRPATH=$1

if [ -z "$DIRPATH" ]; then
    echo "Error"
    echo "Usage: archive_dir.sh <directory>"
    exit 1
fi


DIRPATH=`realpath $DIRPATH`
DIRNAME=`basename $DIRPATH`
PARENT=`dirname $DIRPATH`
OUTPUT="${DIRNAME}.tar"

cd $PARENT

if [ ! -f $OUTPUT ]; then
    echo "Creating $OUTPUT"
    #tar cfv $OUTPUT $DIRNAME
    tar -cv --exclude "*.pdf" -f "${OUTPUT}" "${DIRNAME}"
else
    echo "Updating $OUTPUT"
    # The u flag will only update the tar file with new content
    #tar ufv $OUTPUT $DIRNAME
    tar -cuv -exclude *.pdf -f "${OUTPUT}" "${DIRNAME}"
fi


echo "Output: $PARENT/$OUTPUT"
