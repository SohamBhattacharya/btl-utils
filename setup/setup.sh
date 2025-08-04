#!/bin/bash

for f in $(find python scripts -type f | grep -E ".sh$|.py$" | sort -V); do
    chmod -v +x $f
    git update-index --chmod=+x $f
done

#sudo chmod 666 /dev/ttyS*
#sudo chmod 666 /dev/ttyUSB*
#sudo chmod 666 /dev/ttyACM0
