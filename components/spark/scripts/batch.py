"""
- This module is used to batch transform and load data stored in Google Cloud Storage (GCS)
into BigQuery.
- It reads a gcs uri received through environmental variables
- It filters the data based on certain conditions and then writes the data to BigQuery.
- The specific transformations, filter conditions, and target tables are determined by
environmental variables that are set when the module is run.
- It has 2 main outputs, clean data and triaged data.
- triaged data includes data that does not meet specific conditions and are excluded
for further inspection.
"""
import os
from pyspark.sql import SparkSession
from spark_fns import *
from configs import *


if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("temporaryGcsBucket", str(os.getenv("SPARK_BUCKET")))
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    FILENAME = os.getenv("FILENAME")
    CATEGORY = str(os.getenv("CATEGORY"))
    opts = options[CATEGORY]
    URI = f"gs://{STAGING_BUCKET}/{CATEGORY}/{FILENAME}"
    RUN_DATE = str(os.getenv("RUN_DATE"))
    PARTITION = reformat_date(RUN_DATE, "MONTH")

    process(spark, URI, PARTITION, **opts)
