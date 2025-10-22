#!/bin/bash

DIR=$1

echo "CC1 , CC2 , CC3 , PCCA1 , PCCA2 , PCCB1 , PCCB2 , DM"

for f in $(ls $DIR/temp*.json | sort -V); do
    CC1=$(jq '.CCBOARD.TEMP1' $f)
    CC2=$(jq '.CCBOARD.TEMP2' $f)
    CC3=$(jq '.CCBOARD.TEMP3' $f)
    
    PCCA1=$(jq '.PCCA.TEMP1' $f)
    PCCA2=$(jq '.PCCA.TEMP2' $f)

    PCCB1=$(jq '.PCCB.TEMP1' $f)
    PCCB2=$(jq '.PCCB.TEMP2' $f)

    DM=$(jq '.DM02."0"' $f)

    echo "$CC1 , $CC2 , $CC3 , $PCCA1 , $PCCA2 , $PCCB1 , $PCCB2 , $DM"
done
