#!/bin/bash

for f in $(find python scripts -type f | grep -E ".sh$|.py$" | sort -V); do
    chmod -v +x $f
done
