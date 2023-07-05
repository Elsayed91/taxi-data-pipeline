"""
- This module is used to transform and load data stored in Google Cloud Storage (GCS)
into BigQuery.
- It reads in a list of GCS links and groups the links based on their shared schema.
- It reads in the data from each group of links as a Spark DataFrame and performs a set of
transformations on the data.
- It filters the data based on certain conditions and then writes the data to BigQuery.
- The specific transformations, filter conditions, and target tables are determined by
environmental variables that are set when the module is run.
"""
import os

from pyspark.sql import SparkSession

from configs import *
from spark_fns import *

if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("temporaryGcsBucket", str(os.getenv("SPARK_BUCKET")))
    URI = str(os.getenv("URI"))
    _, SRC_BUCKET, _, SRC_FOLDER = uri_parser(URI)
    CATEGORY = str(os.getenv("CATEGORY"))
    opts = options[CATEGORY]

    blobs = get_gcs_files(SRC_BUCKET, SRC_FOLDER, SRC_FOLDER)
    blobs = list_files(blobs)

    df = get_schema_info(blobs)
    print("df shape is")
    print(len(df))
    lists = schema_groups(df)
    print(lists)
    for l in lists:
        print(f"processing {l}")
        idx = lists.index(l)
        process_initial_load(spark, l, idx, **opts)
        print("finished processing")
