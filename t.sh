#!/bin/bash

source="s3://nyc-tlc/trip data/"

# Extract the part of the s3_source link after the last slash
file_part=${source##*/}
echo $file_part
source=${source%*}
echo $source
if [[ -z "$file_part" ]]; then
    filename="*"
else
    filename=$file_part
fi
