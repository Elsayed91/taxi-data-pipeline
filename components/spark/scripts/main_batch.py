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
    URI = f"gs://{STAGING_BUCKET}/{FILENAME}"
    CATEGORY = str(os.getenv("CATEGORY"))
    MAPPING = options[CATEGORY]["mapping"]
    SUMMARY_QUERY = options[CATEGORY]["summary_query"]
    FILTERS = options[CATEGORY]["filter_conditions"]
    HIST_TARGET = str(os.getenv("HISTORICAL_TARGET"))
    STAGING_TARGET = str(os.getenv("STAGING_TARGET"))
    TRIAGE_TAREGET = str(os.getenv("TRIAGE_TAREGET"))
    RUN_DATE = str(os.getenv("RUN_DATE"))
    PARTITION = reformat_date(RUN_DATE, "MONTH")

    try:
        df = spark.read.parquet(URI)
    except Exception as e:
        print(f"Error reading from BigQuery: {e}")

    df = cast_columns(df, MAPPING)  # type: ignore

    # Create the temporary table
    temp_table = df.createOrReplaceTempView("temp_table")

    df_hist, df_clean, df_triage = process_current(spark, SUMMARY_QUERY, FILTERS)

    write_to_bigquery(df_hist, HIST_TARGET, f"hist-{PARTITION}", PARTITION, "overwrite")
    write_to_bigquery(
        df_clean, STAGING_TARGET, f"clean-{PARTITION}", PARTITION, "overwrite"
    )
    write_to_bigquery(
        df_triage, TRIAGE_TAREGET, f"triage-{PARTITION}", PARTITION, "overwrite"
    )
