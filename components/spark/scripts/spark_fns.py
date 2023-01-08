import pandas as pd
import google.cloud.storage as storage
import pyarrow.parquet as pq
import gcsfs
import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from typing import Union
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp, to_date


def get_gcs_files(bucket: str, folder: str, file_prefix: str) -> list[bytes]:
    """
    Retrieve a list of blobs from the specified bucket with the given folder and file prefix.

    Args:
        bucket: The name of the bucket to list blobs from.
        folder: The folder prefix to use for filtering the list of blobs.
        file_prefix: The file prefix to use for filtering the list of blobs.

    Returns:
        A list of bytes representing the blobs with the given folder and file prefix.

    Raises:
        ValueError: If no blobs are found with the given prefix.
    """
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket, prefix=f"{folder}/{file_prefix}")
    if not blobs:
        raise ValueError("No blobs found with the given prefix.")
    return list(blobs)


def list_files(blobs: list[bytes]) -> list[str]:
    """
    Extract the file names from a list of blobs and return a list of file names.
    Expects Files with format gs://bucket/folder/file
    Args:
        blobs: A list of bytes representing the blobs to extract file names from.

    Returns:
        A list of file names extracted from the blobs.
    """
    list_items = []
    for blob in blobs:
        file_parts = (str(blob)).strip().split(",")
        # file_name = (str(blob).strip().split(",")[-2]).split("/")[-1] =>  yellow/yellow_tripdata_2011-01.parquet
        link = "gs://" + file_parts[0].split(": ")[-1] + "/" + file_parts[-2].strip()
        list_items.append(link)

    return list_items


def get_schema_info(links: list[str]) -> pd.DataFrame:
    """
    Read the schema of items in a list of GCS links by reading the metadata.

    Parameters:
    - links: A list of strings representing the GCS links of the items.

    Returns:
    A DataFrame containing the schema information for each item in `links`.
    The DataFrame has a column `link` that contains the GCS link of each item,
    and one column for each field in the schema of the item, where the column name is the field name and the column value is the field data type.
    """
    df_list = []
    for link in links:
        with gcsfs.GCSFileSystem().open(link) as f:
            schema = pq.read_schema(f, memory_map=True)
            df = pd.DataFrame(
                [
                    {
                        "link": link,
                        **{
                            name: dtype
                            for name, dtype in zip(schema.names, schema.types)
                        },
                    }
                ]
            ).astype(str)
            df_list.append(df)
    return pd.concat(df_list, ignore_index=True)


def schema_groups(df: pd.DataFrame) -> list[list[str]]:
    """
    Group GCS links in a DataFrame by shared schema.

    Parameters:
    - df: A DataFrame containing a column `link` with GCS links and columns representing the fields in the schema of each link.

    Returns:
    A list of lists, where each inner list contains the GCS links that share the same schema. The schema is determined by the column names and values in `df` (excluding the `link` column).
    """
    columns = [value for value in list(df.columns) if value != "link"]
    df_groups = df.groupby(columns)["link"]
    return df_groups.apply(lambda x: list(x)).tolist()


def cast_columns(df: DataFrame, mapping: dict[str, str]) -> DataFrame:
    """
    Cast columns in a DataFrame to corresponding data types according to a mapping dict that is provided.

    Parameters:
    - df: The DataFrame whose columns should be cast.
    - mapping: A dictionary where the keys are column names and the values are the new data types to which the columns should be cast.

    Returns:
    df with columns that are included in the mapping and with the columns cast to appropriate dtype.
    """
    rest_cols = [F.col(cl) for cl in df.columns if cl not in mapping]
    conv_cols = [
        F.col(cl_name).cast(cl_type).alias(cl_name)
        for cl_name, cl_type in mapping.items()
        if cl_name in df.columns
    ]
    cast_df = df.select(*rest_cols, *conv_cols)
    return cast_df


def uri_parser(uri: str) -> tuple[str, str, str, str]:
    """Parses a GCS URI string and returns its parts.

    Args:
        uri (str): The URI string to parse.

    Returns:
        tuple: A tuple containing the following elements:
            - filename (str): The name of the file.
            - bucket (str): The name of the bucket.
            - blob_path (str): The path of the blob.
            - category (str): The category of the file.
    """
    filename = uri.split("/")[-1]
    bucket = uri.split("/")[2]
    blob_path = "/".join(uri.split("/")[3:])
    category = uri.split("/")[-2]
    return filename, bucket, blob_path, category


def reformat_date(date_string: str, output_format: str) -> str:
    """
    Reformats a date string in the format "YYYY-MM-DD" to a different format specified by
    the output_format parameter.

    Parameters: - date_string (str): The date string to reformat. - output_format (str):
    The desired output format for the date. Can be "MONTH", "YEAR", or "DAY".

    Returns: - str: The date in the specified output format.
    """
    year, month, _ = date_string.split("-")
    if output_format == "MONTH":
        return f"{year}{month}"
    elif output_format == "YEAR":
        return year
    elif output_format == "DAY":
        return date_string
    else:
        raise ValueError("Invalid output format")


def process(
    spark: SparkSession,
    uri: str,
    partition_filter: str,
    run_date: str,
    **kwargs,
):
    df = spark.read.parquet(uri)
    df = cast_columns(df, kwargs["mapping"])
    df = df.filter(
        f"{kwargs['partition_col']} BETWEEN CAST({run_date}) AS DATE) \
                AND CAST({run_date}) AS DATE) + INTERVAL 1 MONTH"
    )
    df.createOrReplaceTempView("temp_table")
    df_hist = spark.sql(kwargs["summary_query"])
    df_hist.write.mode("overwrite").format("bigquery").option(
        "datePartition", partition_filter
    ).option("partitionField", kwargs["partition_col_hist"]).option(
        "partitionType", "MONTH"
    ).option(
        "clusteredFields", kwargs["cf_hist"]
    ).option(
        "bigQueryJobLabel.spark", f"hist-{partition_filter}"
    ).save(
        kwargs["historical_table"]
    )
    df_clean = spark.sql(f"SELECT * FROM temp_table WHERE {kwargs['filters']}")
    df_triage = spark.sql(f"SELECT * FROM temp_table WHERE NOT ({kwargs['filters']})")

    shared_options = {
        "datePartition": partition_filter,
        "partitionField": kwargs["partition_col"],
        "partitionType": "MONTH",
        "clusteredFields": kwargs["cf_current"],
    }
    df_clean.write.mode("overwrite").format("bigquery").option(**shared_options).option(
        "bigQueryJobLabel.spark", f"clean-{partition_filter}"
    ).save(kwargs["staging_table"])
    df_triage.write.mode("overwrite").format("bigquery").option(
        **shared_options
    ).option("bigQueryJobLabel.spark", f"triage-{partition_filter}").save(
        kwargs["triage_table"]
    )


def process_initial_load(
    spark: SparkSession,
    uri: Union[str, list[str]],
    idx: int,
    **kwargs,
):
    df = spark.read.parquet(*uri)
    df = cast_columns(df, kwargs["mapping"])
    df.createOrReplaceTempView("temp_table")
    df_hist = spark.sql(kwargs["summary_query"])
    df_hist.write.mode("append").format("bigquery").option(
        "bigQueryJobLabel.spark", f"hist-{idx}"
    ).save(kwargs["historical_table"])
    df = df.filter(
        F.col(kwargs["partition_col"])
        > F.current_timestamp() - F.expr("INTERVAL 6 MONTH")
    )
    df.createOrReplaceTempView("temp_table")
    df_clean = spark.sql(f"SELECT * FROM temp_table WHERE {kwargs['filters']}")
    df_triage = spark.sql(f"SELECT * FROM temp_table WHERE NOT ({kwargs['filters']})")
    df_clean.write.mode("append").format("bigquery").option(
        "bigQueryJobLabel.spark", f"clean-{idx}"
    ).save(kwargs["staging_table"])
    df_triage.write.mode("append").format("bigquery").option(
        "bigQueryJobLabel.spark", f"triage-{idx}"
    ).save(kwargs["triage_table"])
