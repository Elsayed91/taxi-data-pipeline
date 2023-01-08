"""

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
    FILTERS = opts["filters"]
    RUN_DATE = str(os.getenv("RUN_DATE"))
    PARTITION = reformat_date(RUN_DATE, "MONTH")

    process(spark, URI, PARTITION, **opts)
