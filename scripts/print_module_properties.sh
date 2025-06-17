#!/bin/bash

set -eEu

CAT_FILE="$1" # Categorization file (e.g. SensorModule_categorization.yaml)
INFO_FILE="$2" # Module information file (e.g. sm_info.yaml)

CATEGORY="$3" # Module category (e.g. A)
PROPERTY="$4" # Module property (e.g. lyso)

for bc in $(yq ".modules.$CATEGORY[]" < $CAT_FILE); do
    yq -r ".$bc.$PROPERTY" < $INFO_FILE
done | sort -V