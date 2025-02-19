#!/bin/bash -x

set -eEu

DIR=/run/media/cptlab/qaqc_data/results/QAQC_SM/qaqc-gui_output/SM_QAQC_Production
SRC=${DIR}.tar
DST=btl-upload@login-2.ultralight.org:upload/QAQC_SM/qaqc-gui_output/

# Archive the directory
./scripts/archive_dir.sh /run/media/cptlab/qaqc_data/results/QAQC_SM/qaqc-gui_output/SM_QAQC_Production

# Copy the archive to the remote server
sftp -r $DST <<< "put $SRC ."