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
from fix_schema import *
from configs import *
from pyspark.sql import SparkSession


URI = str(os.getenv("URI"))
_, SRC_BUCKET, _, SRC_FOLDER = uri_parser(URI)
CATEGORY = str(os.getenv("CATEGORY"))
MAPPING = options[CATEGORY]["mapping"]
FILTER_CONDITION = options[CATEGORY]["filter_condition"]
TRANSFORMATION_QUERY = options[CATEGORY]["transformation_query"]

LABEL_KEY = str(os.getenv("LABEL", "spark-etl"))
HISTORICAL_TARGET = str(os.getenv("HISTORICAL_TARGET"))
STAGING_TARGET = str(os.getenv("STAGING_TARGET"))
TRIAGE_TAREGET = str(os.getenv("TRIAGE_TAREGET"))

if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("temporaryGcsBucket", str(os.getenv("SPARK_BUCKET")))

    blobs = get_gcs_files(SRC_BUCKET, SRC_FOLDER, SRC_FOLDER)
    blobs = list_files(blobs)
    df = get_schema_info(blobs)
    lists = schema_groups(df)
    for l in lists:
        idx = lists.index(l)
        df = spark.read.parquet(*l)
        df = cast_columns(df, MAPPING)  # type: ignore
        df_view = df.createOrReplaceTempView("df_view")
        df_historical = spark.sql(TRANSFORMATION_QUERY)
        df_historical.write.mode("append").format("bigquery").option(
            "bigQueryJobLabel.spark", f"etl-hist-{idx}"
        ).save(HISTORICAL_TARGET)
        df_current = df.filter(
            F.col("tpep_pickup_datetime")
            > F.current_timestamp() - F.expr("INTERVAL 6 MONTH")
        )
        df_current_clean = df.filter(FILTER_CONDITION)
        df_current_trash = df.filter(~FILTER_CONDITION)  # type: ignore
        df_current_clean.write.mode("append").format("bigquery").option(
            "bigQueryJobLabel.spark", f"etl-clean-{idx}"
        ).save(STAGING_TARGET)
        df_current_trash.write.mode("append").format("bigquery").option(
            "bigQueryJobLabel.spark", f"etl-triage{idx}"
        ).save(TRIAGE_TAREGET)
