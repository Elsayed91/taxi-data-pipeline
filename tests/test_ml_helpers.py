import unittest
from components.ml_serve.scripts.helpers import PredictionAssistant
import pandas as pd
import numpy as np
from unittest import mock
import json
import requests


class TestPredictionAssistant(unittest.TestCase):
    def test_merge_geo_data(self):
        inputs = {
            "passenger_count": 1,
            "pickup_zone": "Arden Heights",
            "dropoff_zone": "Newark Airport",
        }

        pa = PredictionAssistant(inputs, "components/ml_serve/scripts/zones.csv")
        df = pa.df1
        result = pa.merge_geo_data(df, "pickup")
        result = pa.merge_geo_data(result, "dropoff")
        result = result.drop(
            ["LocationID_x", "borough_x", "LocationID_y", "borough_y"], axis=1
        )

        expected_result = pd.DataFrame(
            {
                "passenger_count": [1],
                "pickup_long": [-74.18755828249991],
                "pickup_lat": [40.55066406499992],
                "dropoff_long": [-74.17153349999995],
                "dropoff_lat": [40.68948349999988],
            }
        )

        self.assertTrue(result.equals(expected_result))

    @mock.patch("requests.get")
    def test_get_trip_duration(self, mock_get):
        df = pd.DataFrame(
            {
                "passenger_count": [1],
                "pickup_long": [-74.187558],
                "pickup_lat": [40.550664],
                "dropoff_long": [-74.171533],
                "dropoff_lat": [40.689483],
            }
        )

        # Define the mock API response
        mock_response = mock.Mock()
        mock_response.content = json.dumps(
            {
                "code": "Ok",
                "routes": [
                    {
                        "weight_name": "routability",
                        "weight": 1579.7,
                        "duration": 1579.7,
                        "distance": 22344.3,
                    }
                ],
            }
        )

        # Configure the mock API call to return the predefined response
        mock_get.return_value = mock_response

        pa = PredictionAssistant({}, "components/ml_serve/scripts/zones.csv")
        result = pa.get_trip_duration(df)

        expected_result = 26  # 1579.7 / 60
        self.assertEqual(result, expected_result)

    def test_haversine_distance(self):
        pa = PredictionAssistant({}, "components/ml_serve/scripts/zones.csv")
        start_lat = 40.7128
        start_lng = -74.0060
        end_lat = 41.8818
        end_lng = -87.6298

        expected_distance = 711.03843176
        computed_distance = pa.haversine_distance(
            start_lat, start_lng, end_lat, end_lng
        )

        self.assertAlmostEqual(computed_distance, expected_distance, delta=0.001)

    def test_add_distances_from_airport(self):
        df = pd.DataFrame(
            {
                "passengers": [1],
                "pickup_long": [-74.187558],
                "pickup_lat": [40.550664],
                "dropoff_long": [-74.171533],
                "dropoff_lat": [40.689483],
            }
        )

        expected_result = pd.DataFrame(
            {
                "passengers": [1],
                "pickup_long": [-74.187558],
                "pickup_lat": [40.550664],
                "dropoff_long": [-74.171533],
                "dropoff_lat": [40.689483],
                "pickup_jfk_distance": [22.306055],
                "dropoff_jfk_distance": [20.863664],
                "pickup_ewr_distance": [9.850164],
                "dropoff_ewr_distance": [0.258613],
                "pickup_lga_distance": [22.749948],
                "dropoff_lga_distance": [16.784075],
            }
        )
        pa = PredictionAssistant({}, "components/ml_serve/scripts/zones.csv")
        result = pa.distance_from_airport(df)

        # Check if the result is a pandas DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        np.testing.assert_allclose(
            result.values, expected_result.values, rtol=0.001, atol=0.001
        )

    def test_prepare(self):
        # Sample input
        data = {
            "passengers": [1],
            "pickup_long": [-74.187558],
            "pickup_lat": [40.550664],
            "dropoff_long": [-74.171533],
            "dropoff_lat": [40.689483],
        }
        df = pd.DataFrame(data)

        # Expected output
        expected = {
            "passengers": [1],
            "pickup_long": [-74.187558],
            "pickup_lat": [40.550664],
            "dropoff_long": [-74.171533],
            "dropoff_lat": [40.689483],
            "trip_duration": [26],
            "day": [10],
            "month": [2],
            "year": [2023],
            "day_of_week": [4],
            "hour": [15],
            "trip_distance": [2.83962],
            "pickup_jfk_distance": [22.306055],
            "dropoff_jfk_distance": [20.863664],
            "pickup_ewr_distance": [9.850164],
            "dropoff_ewr_distance": [0.258613],
            "pickup_lga_distance": [22.749948],
            "dropoff_lga_distance": [16.784075],
        }
        expected = pd.DataFrame(expected)

        # Call the prepare method
        result = PredictionAssistant(
            data, "components/ml_serve/scripts/zones.csv"
        ).prepare()

        # Check if the result is equal to the expected output
        pd.testing.assert_frame_equal(result, expected)
