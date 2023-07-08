"""
This module is for a New York taxi fare prediction application that uses Streamlit for
user interface and Mlflow for model deployment. The main function `run` accepts two
parameters and starts the app by loading the zones data and creating the UI, then it runs
prediction on the inputted parameters when the Predict button is clicked.

The Streamlit app has implemented model caching and error handling to ensure a smooth user
experience. If there's a problem with the server connection, the app can be reloaded, but
once it's connected, the cached model will be available for use even if Streamlit re-reads
the entire app when an element is updated. This remains the case even if there's a
connection issue later on.
"""
import os

import pandas as pd
import streamlit as st

from serve_utils import *


def run(mlflow_uri: str, mlflow_experiment_name: str) -> None:
    """
    Starts the taxi fare prediction app. It accepts two parameters, the Mlflow URI and the
    name of the Mlflow experiment that holds the model, then creates the user interface
    and predicts the fare based on the inputted parameters when the Predict button is
    clicked.

    Args:
    - mlflow_uri (str): the URI of the Mlflow server
    - mlflow_experiment_name (str): the name of the Mlflow experiment

    Returns:
    None
    """
    st.title("New York Taxi Fare Predictor")
    df = pd.read_csv("zones.csv")
    passengers = st.number_input("Passengers", min_value=1, max_value=7, value=1)
    borough_options = df["borough"].unique()
    borough_options = ["All"] + list(borough_options)
    default_ix = borough_options.index("All")
    pickup_borough = st.selectbox("Pickup Borough", borough_options, index=default_ix)
    dropoff_borough = st.selectbox("Dropoff Borough", borough_options, index=default_ix)
    if pickup_borough == "All":
        pickup_zone_options = df["zone"].unique()
    else:
        pickup_zone_options = df[df["borough"] == pickup_borough]["zone"].unique()
    pickup_zone = st.selectbox("Pickup Zone", pickup_zone_options)
    if dropoff_borough == "All":
        dropoff_zone_options = df["zone"].unique()
    else:
        dropoff_zone_options = df[df["borough"] == dropoff_borough]["zone"].unique()
    dropoff_zone = st.selectbox("Dropoff Zone", dropoff_zone_options)
    output = ""

    input_dict = {
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "passengers": passengers,
    }
    input_df = pd.DataFrame([input_dict])
    if st.button("Predict"):
        try:
            df = PredictionAssistant(input_df, "zones.csv").prepare()
            output = model.predict(df)
            output = "$" + str(round(output[0], 2))
        except:
            st.error(
                "Something went wrong. Please reload the page.",
                icon="🚨",
            )

    st.success(f"Estimated fare is {output}")


@st.cache_resource
def cached_model(mlflow_uri, mlflow_experiment_name):
    if check_connection(mlflow_uri):
        return load_model(mlflow_uri, mlflow_experiment_name)


if __name__ == "__main__":
    mlflow_uri = os.getenv("MLFLOW_URI")
    mlflow_experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME")

    model = cached_model(mlflow_uri, mlflow_experiment_name)
    if model:
        run(model, mlflow_experiment_name)
    else:
        st.info(
            "Something went wrong with the server connection."
            + "Click on **Check Connection** to try again.",
            icon="🚨",
        )
        if st.button("Check Connection"):
            st.cache_resource.clear()
