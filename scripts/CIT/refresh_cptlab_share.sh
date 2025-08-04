#!/bin/bash

DIR="$1"
OPTS=""

if [ -n "$DIR" ]; then
  OPTS="dir=$DIR"
fi

rclone -v rc vfs/refresh recursive=true --fast-list $OPTS
