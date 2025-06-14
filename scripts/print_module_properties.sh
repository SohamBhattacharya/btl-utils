#!/bin/bash

set -eEu

CAT_FILE="$1"
INFO_FILE="$2"

CATEGORY="$3"
PROPERTY="$4"

for bc in $(yq ".modules.$CATEGORY[]" < $CAT_FILE); do
    yq -r ".$bc.$PROPERTY" < $INFO_FILE
done | sort -V