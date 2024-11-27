#!/bin/bash

USER=$1

ssh -f -N -L 8113:dbloader-mtd.cern.ch:8113 $USER@lxplus.cern.ch

