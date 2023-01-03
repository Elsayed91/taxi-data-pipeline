import logging
from typing import List
import pandas as pd
import google.cloud.storage as storage
import pyarrow.parquet as pq
import gcsfs
import pyspark.sql.functions as F
from pyspark.sql import SparkSession
import os

try:
    from configs import yellow_schema_mapping
except:
    from components.spark.scripts.configs import *


def get_gcs_files(bucket: str, folder: str, file_prefix: str) -> List[bytes]:
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


def list_files(blobs: List[bytes]) -> List[str]:
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


def get_schema_info(links: List[str]) -> pd.DataFrame:
    """
    reads the schema of items in a list by reading the metadata.
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


def schema_groups(df: pd.DataFrame):
    """creates a list holding lists of links of files that share the same schema."""
    columns = [value for value in list(df.columns) if value != "link"]
    df_groups = df.groupby(columns)["link"]
    return df_groups.apply(lambda x: list(x)).tolist()


def cast_columns(df, mapping):
    rest_cols = [F.col(cl) for cl in df.columns if cl not in mapping]
    conv_cols = [
        F.col(cl_name).cast(cl_type).alias(cl_name)
        for cl_name, cl_type in mapping.items()
        if cl_name in df.columns
    ]
    cast_df = df.select(*rest_cols, *conv_cols)
    return cast_df


def uri_parser(uri: str) -> tuple[str, str, str, str]:
    """Parses a URI string and returns its parts.

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


if __name__ == "__main__":
    URI = os.getenv("URI")
    NAME_PREFIX = os.getenv("NAME_PREFIX")
    _, SRC_BUCKET, _, SRC_FOLDER = uri_parser(URI)  # type: ignore
    spark = SparkSession.builder.getOrCreate()
    blobs = get_gcs_files(SRC_BUCKET, SRC_FOLDER, SRC_FOLDER)  # type: ignore
    blobs = list_files(blobs)  # type: ignore
    df = get_schema_info(blobs)  # type: ignore
    lists = schema_groups(df)
    for l in lists:
        df = spark.read.parquet(*l)
        df = cast_columns(df, yellow_schema_mapping)
        year_month = F.to_date(F.col(PARTITION_COLUMN), "YYYY-MM")  # type: ignore
        df_with_partition = df.withColumn("year_month", year_month)
        df_with_partition.write.partitionBy("year_month").mode("append").parquet(
            f"gs://{SRC_BUCKET}/{SRC_FOLDER}/{NAME_PREFIX}"
        )
