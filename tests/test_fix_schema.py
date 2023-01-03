import pytest
from unittest.mock import patch
from components.spark.scripts.fix_schema import *
import mock
import pyarrow.parquet as pq
import google.cloud.storage as storage
from components.spark.scripts.configs import *
import pyarrow as pa
import unittest.mock
import unittest
import pandas as pd
import tempfile
from pyspark.sql import SparkSession


@pytest.mark.parametrize(
    "bucket, folder, file_prefix, expected_output",
    [
        (
            "my-bucket",
            "my-folder",
            "my-prefix",
            ["blob1", "blob2"],
        ),  # Test case: Successful retrieval of blobs
        ("my-bucket", "my-folder", "my-prefix", []),  # Test case: No blobs found
    ],
)
def test_get_gcs_files(bucket: str, folder: str, file_prefix: str, expected_output):
    """
    mocks the Client class and the list_blobs method of the google.cloud.storage module,
    and tests the get_files function with the given arguments and expected output.
    If expected_output is falsy, the test function expects the get_files function
    to raise a ValueError with the message "No blobs found with the given prefix."
    The test function then asserts that this error is raised.
    """
    with mock.patch.object(storage, "Client") as mock_client:
        mock_client.return_value.list_blobs.return_value = expected_output
        if expected_output:
            assert get_gcs_files(bucket, folder, file_prefix) == expected_output
        else:
            try:
                get_gcs_files(bucket, folder, file_prefix)
                assert False, "Expected ValueError to be raised."
            except ValueError as e:
                assert str(e) == "No blobs found with the given prefix."


def test_list_files():
    """
    Test that the list_files function correctly extracts file names from a list of blobs.
    """
    blobs = [
        b"<Blob: raw-8d74c9728b, yellow/yellow_tripdata_2011-01.parquet, 1672605643118080>",
        b"<Blob: raw-8d74c9728b, yellow/yellow_tripdata_2020-12.csv, 1672605645903144>",
        b"<Blob: test-8d7dassddab, yellow/green_tripdata_2011-02.txt, 1672605645903144>",
    ]
    expected_output = [
        "gs://raw-8d74c9728b/yellow/yellow_tripdata_2011-01.parquet",
        "gs://raw-8d74c9728b/yellow/yellow_tripdata_2020-12.csv",
        "gs://test-8d7dassddab/yellow/green_tripdata_2011-02.txt",
    ]

    assert list_files(blobs) == expected_output


@pytest.fixture
def schema():
    return pa.schema(
        [
            pa.field("VendorID", pa.int64()),
            pa.field("tpep_pickup_datetime", pa.timestamp("us")),
            pa.field("tpep_dropoff_datetime", pa.timestamp("us")),
            pa.field("passenger_count", pa.int64()),
            pa.field("trip_distance", pa.float64()),
            pa.field("RatecodeID", pa.int64()),
            pa.field("store_and_fwd_flag", pa.string()),
            pa.field("PULocationID", pa.int64()),
            pa.field("DOLocationID", pa.int64()),
            pa.field("payment_type", pa.int64()),
            pa.field("fare_amount", pa.float64()),
            pa.field("extra", pa.float64()),
            pa.field("mta_tax", pa.float64()),
            pa.field("tip_amount", pa.float64()),
            pa.field("tolls_amount", pa.float64()),
            pa.field("improvement_surcharge", pa.float64()),
            pa.field("total_amount", pa.float64()),
            pa.field("congestion_surcharge", pa.float64()),
            pa.field("airport_fee", pa.float64()),
        ]
    )


class TestGetSchemaInfo(unittest.TestCase):
    def setUp(self):

        self.df = pd.DataFrame(
            {
                "VendorID": [1, 2, 1],
                "passenger_count": [1, 2, 1],
                "store_and_fwd_flag": ["Y", "N", "Y"],
            }
        )

        df = pa.Table.from_pandas(self.df)
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
        pq.write_table(df, self.temp_file.name)

    @patch("gcsfs.GCSFileSystem")
    def test_get_schema_info(self, mock_gcsfs):

        mock_open = mock_gcsfs.return_value.open
        mock_open.return_value = self.temp_file

        result = get_schema_info([self.temp_file.name])
        print(result)
        # Assert that the resulting DataFrame has the correct schema
        self.assertEqual(
            list(result.columns),
            ["link", "VendorID", "passenger_count", "store_and_fwd_flag"],
        )
        self.assertEqual(list(result["VendorID"]), ["int64"])
        self.assertEqual(list(result["passenger_count"]), ["int64"])
        self.assertEqual(list(result["store_and_fwd_flag"]), ["string"])

    def tearDown(self):
        # Delete the temporary file
        import os

        os.unlink(self.temp_file.name)


def test_schema_groups():
    test_data = {
        "store_and_fwd_flag": ["int64", "int64", "int64", "int64"],
        "tip_amount": ["int64", "int64", "int64", "int64"],
        "tolls_amount": ["int64", "int64", "int64", "int64"],
        "airport_fee": ["double", "int64", "double", "int64"],
        "link": [
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-01.csv",
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-02.csv",
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-03.csv",
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-04.csv",
        ],
    }
    df = pd.DataFrame(test_data)

    expected_output = [
        [
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-01.csv",
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-03.csv",
        ],
        [
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-02.csv",
            "gs://raw-8d74c9728b/yellow/yellow_tripdata_2019-04.csv",
        ],
    ]

    assert schema_groups(df) == expected_output


# @pytest.fixture
# def spark_session():
#     from pyspark.sql import SparkSession

#     spark = SparkSession.builder.appName("test").master("local[*]").getOrCreate()
#     yield spark
#     spark.stop()


def test_cast_columns(spark_session):
    # Create a test DataFrame
    df = spark_session.createDataFrame(
        [
            (1, "2022-01-01 12:34:56", "2022-01-01 12:45:23", 1, 2.5, 1, 100.0),
            (2, "2022-02-01 13:34:56", "2022-02-01 13:45:23", 3, 3.5, 2, 150.0),
        ],
        schema=[
            "VendorID",
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "passenger_count",
            "trip_distance",
            "RatecodeID",
            "fare_amount",
        ],
    )

    # Define the mapping of column names to target data types
    mapping = {
        "VendorID": "integer",
        "tpep_pickup_datetime": "timestamp",
        "tpep_dropoff_datetime": "timestamp",
        "passenger_count": "integer",
        "trip_distance": "float",
        "RatecodeID": "integer",
    }

    # Cast the columns of the DataFrame using the function
    casted_df = cast_columns(df, mapping)

    # Check that the data types of the columns were updated correctly
    from pyspark.sql.types import IntegerType, TimestampType, FloatType

    assert casted_df.schema["VendorID"].dataType == IntegerType()
    assert casted_df.schema["tpep_pickup_datetime"].dataType == TimestampType()
    assert casted_df.schema["tpep_dropoff_datetime"].dataType == TimestampType()
    assert casted_df.schema["passenger_count"].dataType == IntegerType()
    assert casted_df.schema["trip_distance"].dataType == FloatType()
    assert casted_df.schema["RatecodeID"].dataType == IntegerType()


def test_uri_parser():
    uri = "gs://bucket/folder/category/category_name_2022-01.extension"
    expected_output = (
        "category_name_2022-01.extension",
        "bucket",
        "folder/category/category_name_2022-01.extension",
        "category",
    )
    assert uri_parser(uri) == expected_output

    uri = "gs://another_bucket/another_folder/another_category/another_name_2022-02.extension"
    expected_output = (
        "another_name_2022-02.extension",
        "another_bucket",
        "another_folder/another_category/another_name_2022-02.extension",
        "another_category",
    )
    assert uri_parser(uri) == expected_output


def test_yellow_filter_conditions():

    spark = SparkSession.builder.getOrCreate()
    df = spark.createDataFrame(
        [
            {
                "tpep_pickup_datetime": "2022-01-01 10:00:00",
                "tpep_dropoff_datetime": "2022-01-01 11:00:00",
                "passenger_count": 1,
                "VendorID": 1,
                "RatecodeID": 1,
                "payment_type": 1,
                "fare_amount": 10.0,
                "DOLocationID": 1,
                "PULocationID": 2,
                "trip_distance": 10.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 11:00:00",
                "tpep_dropoff_datetime": "2022-01-01 12:00:00",
                "passenger_count": 2,
                "VendorID": 2,
                "RatecodeID": 2,
                "payment_type": 2,
                "fare_amount": 20.0,
                "DOLocationID": 2,
                "PULocationID": 3,
                "trip_distance": 20.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 12:00:00",
                "tpep_dropoff_datetime": "2022-01-01 13:00:00",
                "passenger_count": 3,
                "VendorID": 3,
                "RatecodeID": 3,
                "payment_type": 3,
                "fare_amount": 30.0,
                "DOLocationID": 3,
                "PULocationID": 4,
                "trip_distance": 30.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 13:00:00",
                "tpep_dropoff_datetime": "2022-01-01 14:00:00",
                "passenger_count": 4,
                "VendorID": 1,
                "RatecodeID": 4,
                "payment_type": 4,
                "fare_amount": 40.0,
                "DOLocationID": None,
                "PULocationID": 5,
                "trip_distance": 40.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 14:00:00",
                "tpep_dropoff_datetime": "2022-01-01 15:00:00",
                "passenger_count": 5,
                "VendorID": 2,
                "RatecodeID": 5,
                "payment_type": 5,
                "fare_amount": 50.0,
                "DOLocationID": 5,
                "PULocationID": 6,
                "trip_distance": 50.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 15:00:00",
                "tpep_dropoff_datetime": "2022-01-01 16:00:00",
                "passenger_count": 6,
                "VendorID": 3,
                "RatecodeID": 6,
                "payment_type": 6,
                "fare_amount": 60.0,
                "DOLocationID": 6,
                "PULocationID": 7,
                "trip_distance": 60.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 16:00:00",
                "tpep_dropoff_datetime": "2022-01-01 17:00:00",
                "passenger_count": 7,
                "VendorID": 1,
                "RatecodeID": 7,
                "payment_type": 7,
                "fare_amount": 70.0,
                "DOLocationID": 7,
                "PULocationID": 8,
                "trip_distance": 70.0,
            },
            {
                "tpep_pickup_datetime": "2022-01-01 17:00:00",
                "tpep_dropoff_datetime": "2022-01-01 18:00:00",
                "passenger_count": 8,
                "VendorID": 2,
                "RatecodeID": 1,
                "payment_type": 1,
                "fare_amount": 80.0,
                "DOLocationID": 8,
                "PULocationID": 9,
                "trip_distance": 80.0,
            },
        ]
    )
    cond = yellow_filter_conditions()
    df_filtered = df.filter(cond)
    assert df_filtered.count() == 6
    df_filtered = df.filter(cond)
    assert df_filtered.filter(F.col("DOLocationID").isNull()).count() == 0
