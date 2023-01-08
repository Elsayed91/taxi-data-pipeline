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
from spark_fns import *
from configs import *
from pyspark.sql import SparkSession


if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("temporaryGcsBucket", str(os.getenv("SPARK_BUCKET")))
    URI = str(os.getenv("URI"))
    _, SRC_BUCKET, _, SRC_FOLDER = uri_parser(URI)
    CATEGORY = str(os.getenv("CATEGORY"))
    MAPPING = options[CATEGORY]["mapping"]
    TRANSFORMATION_QUERY = options[CATEGORY]["transformation_query"]
    FILTERS = options[CATEGORY]["filter_conditions"]
    HIST_TARGET = str(os.getenv("HISTORICAL_TARGET"))
    STAGING_TARGET = str(os.getenv("STAGING_TARGET"))
    TRIAGE_TAREGET = str(os.getenv("TRIAGE_TAREGET"))

    blobs = get_gcs_files(SRC_BUCKET, SRC_FOLDER, SRC_FOLDER)
    blobs = list_files(blobs)
    df = get_schema_info(blobs)
    lists = schema_groups(df)
    for l in lists:
        idx = lists.index(l)
        create_temptable(spark, l, MAPPING)
        df_hist = spark.sql(TRANSFORMATION_QUERY)
        write_to_bigquery(df_hist, HIST_TARGET, f"hist-{idx}")
        create_temptable(spark, l, MAPPING, date_filter=True)
        df_clean, df_triage = process_current(spark, FILTERS)
        write_to_bigquery(df_clean, STAGING_TARGET, f"clean-{idx}")
        write_to_bigquery(df_triage, f"{TRIAGE_TAREGET}", f"triage-{idx}")
