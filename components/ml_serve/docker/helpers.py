import pandas as pd
import datetime
import json
import os
import requests
import numpy as np


class PredictionAssistant:
    """
    A class that helps prepare data to be used by a model, by adding columns that are
    needed to make a prediction.

    Attributes
    inputs : pandas.DataFrame
        The input data with columns: "passenger_count", "pickup_zone", "dropoff_zone".
    zones : pandas.DataFrame
        The data from the CSV file with zone information.

    """

    def __init__(self, inputs, zones_csv):
        self.inputs = inputs
        self.zones = pd.read_csv(zones_csv)

    def merge_geo_data(self, inputs, prefix: str) -> pd.DataFrame:
        """
        Merges the input data with the zones data to add the longitude and latitude
        information.

        Args:
        prefix (str): The prefix for the columns in the input data (either "pickup" or
        "dropoff").

        Returns:
        pd.DataFrame: The input data with the added longitude and latitude information.
        """
        df = pd.merge(
            inputs,
            self.zones,
            how="left",
            left_on=[prefix + "_zone"],
            right_on=["zone"],
        )
        df.rename(
            columns={"longitude": prefix + "_long", "latitude": prefix + "_lat"},
            inplace=True,
        )
        df.drop(["zone", prefix + "_zone"], axis=1, inplace=True)
        return df

    def get_trip_duration(self, df: pd.DataFrame) -> int:
        """
        Calculates the estimated trip duration between pickup and dropoff locations
        by making an API call to OSRM route service.

        Args:
        df (pd.DataFrame): A pandas dataframe containing pickup and dropoff locations.
        It should contain columns "pickup_long", "pickup_lat", "dropoff_long",
        "dropoff_lat".

        Returns:
        int: The estimated trip duration in minutes.

        """
        r = requests.get(
            f"http://router.project-osrm.org/route/v1/car/{df.pickup_long[0]},{df.pickup_lat[0]};{df.dropoff_long[0]},{df.dropoff_lat[0]}?overview=false"
            ""
        )
        routes = json.loads(r.content)
        trip_duration = routes.get("routes")[0]["duration"]
        return round(trip_duration / 60)

    def haversine_distance(
        self, s_lat: float, s_lng: float, e_lat: float, e_lng: float
    ) -> float:
        """
        Calculates the haversine distance between two points on the Earth's surface.

        Args:
        s_lat: Latitude of the start point in degrees
        s_lng: Longitude of the start point in degrees
        e_lat: Latitude of the end point in degrees
        e_lng: Longitude of the end point in degrees

        Returns:
        float: Haversine distance between the two points in miles
        """
        R = 3958.756  # approximate radius of earth in miles
        s_lat, s_lng, e_lat, e_lng = map(np.deg2rad, [s_lat, s_lng, e_lat, e_lng])
        d = (
            np.sin((e_lat - s_lat) / 2) ** 2
            + np.cos(s_lat) * np.cos(e_lat) * np.sin((e_lng - s_lng) / 2) ** 2
        )
        return 2 * R * np.arcsin(np.sqrt(d))

    def distance_from_airport(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds columns to a given dataframe with distances from JFK, EWR, and LGA airports
        to the pickup and dropoff locations.

        Args:
        df (pd.DataFrame): The input dataframe.

        Returns:
        pd.DataFrame: The modified dataframe with new columns for distances from JFK, EWR,
        and LGA airports.
        """
        airports = {
            "jfk": (40.639722, -73.778889),
            "ewr": (40.6925, -74.168611),
            "lga": (40.77725, -73.872611),
        }

        for airport, coords in airports.items():
            df[f"pickup_{airport}_distance"] = self.haversine_distance(
                coords[0], coords[1], df.pickup_lat, df.pickup_long
            )
            df[f"dropoff_{airport}_distance"] = self.haversine_distance(
                coords[0], coords[1], df.dropoff_lat, df.dropoff_long
            )

        return df

    def prepare(self) -> pd.DataFrame:
        """
        This method prepares the taxi ride data for analysis. It merges the pickup and
        dropoff location data with the NYC taxi zone data, calculates the trip duration,
        adds various date-time related features, calculates the trip distance, and adds
        the distances from JFK, EWR and LGA airports to the pickup and dropoff locations.

        Returns:
        pd.DataFrame: The prepared taxi ride data.
        """
        now = datetime.datetime.now()
        df = self.merge_geo_data(self.inputs, "pickup")
        df = self.merge_geo_data(df, "dropoff")
        df = df.drop(["LocationID_x", "borough_x", "LocationID_y", "borough_y"], axis=1)
        df["trip_duration"] = self.get_trip_duration(df)
        df["day"] = now.day
        df["month"] = now.month
        df["year"] = now.year
        df["day_of_week"] = now.weekday()
        df["hour"] = now.hour
        df["trip_distance"] = self.haversine_distance(
            df.pickup_long, df.pickup_lat, df.dropoff_long, df.dropoff_lat
        )
        df = self.distance_from_airport(df)
        return df
