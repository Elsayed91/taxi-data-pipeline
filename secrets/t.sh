#!/bin/bash

s3_source="s3://nyc-tlc/trip data/"

# Extract the part of the s3_source link after the last slash
file_part=${s3_source##*/}

if [[ -z "$file_part" ]]; then
    filename="*"
else
    filename=$file_part
fi
