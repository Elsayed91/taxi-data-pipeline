"""

"""
import os
from pyspark.sql import SparkSession
from spark_fns import *
from configs import *


if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("temporaryGcsBucket", str(os.getenv("SPARK_BUCKET")))
    LABEL_KEY = "bigQueryJobLabel.spark"
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    FILENAME = os.getenv("FILENAME")
    CATEGORY = str(os.getenv("CATEGORY"))
    opts = options[CATEGORY]
    URI = f"gs://{STAGING_BUCKET}/{CATEGORY}/{FILENAME}"
    MAPPING = opts["mapping"]
    SUMMARY_QUERY = opts["summary_query"]
    FILTERS = opts["filter_conditions"]
    HIST_TARGET = opts["historical_table"]
    STAGING_TARGET = opts["staging_table"]
    TRIAGE_TAREGET = opts["triage_table"]
    RUN_DATE = str(os.getenv("RUN_DATE"))
    PARTITION = reformat_date(RUN_DATE, "MONTH")

    process(spark, URI, MAPPING, PARTITION, **opts)
