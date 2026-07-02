#!/bin/bash

# Will list modules in INFO_YML that are not in CAT_YML

INFO_YML="$1"
CAT_YML="$2"

for bc in $(yq .[].barcode "${INFO_YML}"); do
    if [ $(grep -c "${bc}" "${CAT_YML}") == 0 ]; then
        echo "${bc}"
    fi
done
