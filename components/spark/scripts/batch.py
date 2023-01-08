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
    URI = f"gs://{STAGING_BUCKET}/{CATEGORY}/{FILENAME}"
    MAPPING = options[CATEGORY]["mapping"]
    SUMMARY_QUERY = options[CATEGORY]["summary_query"]
    FILTERS = options[CATEGORY]["filter_conditions"]
    HIST_TARGET = options[CATEGORY]["historical_table"]
    STAGING_TARGET = options[CATEGORY]["staging_table"]
    TRIAGE_TAREGET = options[CATEGORY]["triage_table"]
    RUN_DATE = str(os.getenv("RUN_DATE"))
    PARTITION = reformat_date(RUN_DATE, "MONTH")
    create_temptable(spark, URI, MAPPING)
    df_hist = spark.sql(SUMMARY_QUERY)
    df_clean, df_triage = process_current(spark, FILTERS)
    write_to_bigquery(df_hist, HIST_TARGET, f"hist-{PARTITION}", PARTITION)
    write_to_bigquery(df_clean, STAGING_TARGET, f"c-{PARTITION}", PARTITION)
    write_to_bigquery(df_triage, TRIAGE_TAREGET, f"t-{PARTITION}", PARTITION)