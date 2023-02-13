import unittest
from unittest.mock import Mock
import pandas as pd
from typing import Optional
from components.ml_train.scripts.train_utils import load_data
from unittest.mock import patch
from dotenv import load_dotenv
import os

load_dotenv(".env")
dataset = os.getenv("SEEDS_DATASET")
table = os.getenv("SEEDS_TABLE", "seed_zones")


def test_load_data():
    sample_size = 10
    query = f"""SELECT * FROM `{dataset}`.`{table}`"""
    df = load_data(query=query, sample_size=sample_size)

    # Test the shape of the returned DataFrame
    assert df.shape == (sample_size, 5)

    # Test if the sample size is less than or equal to the maximum allowed size
    assert df.shape[0] <= sample_size
    # Test if the data frame contains the expected columns
    assert set(df.columns) == {"LocationID", "borough", "zone", "longitude", "latitude"}

    # Test if the values in the 'borough' column are all strings
    assert all(isinstance(value, str) for value in df["borough"])

    # Test if the values in the 'zone' column are all strings
    assert all(isinstance(value, str) for value in df["zone"])

    # Test if the values in the 'longitude' column are all floats
    assert all(isinstance(value, float) for value in df["longitude"])

    # Test if the values in the 'latitude' column are all floats
    assert all(isinstance(value, float) for value in df["latitude"])


class TestLoadDataUselessMock(unittest.TestCase):
    def test_load_data(self):
        # Create a mock DataFrame
        mock_df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        def mock_read_gbq(*args, **kwargs):
            max_results = kwargs.get("max_results", None)
            if max_results:
                return mock_df.head(max_results)
            return mock_df

        pd.read_gbq = Mock(side_effect=mock_read_gbq)

        # Call the load_data function with sample size 1
        result = load_data("test_dataset", "test_table", 2)

        # Assert that the returned value is equal to the mock DataFrame
        self.assertEqual(result.equals(mock_df.head(2)), True)
