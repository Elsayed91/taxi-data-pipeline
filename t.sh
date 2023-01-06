#!/bin/bash

source="s3://nyc-tlc/trip data/"
source2="s3://nyc-tlc/trip data/yellow_tripdata_2022-10.parquet"
# Extract the part of the s3_source link after the last slash

source=${source%/*}
echo $source

source2=${source2%/*}/
echo $source2
