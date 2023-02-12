"""
This module is for a New York taxi fare prediction application that uses Streamlit for
user interface and Mlflow for model deployment. The main function `run` accepts two
parameters and starts the app by loading the zones data and creating the UI, then it runs
prediction on the inputted parameters when the Predict button is clicked.
"""
import streamlit as st
import pandas as pd
from helpers import PredictionAssistant, load_model
import os


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
            model = load_model(mlflow_uri, mlflow_experiment_name)
            output = model.predict(df)
            output = "$" + str(round(output[0], 2))
        except Exception as e:
            st.error(
                "There was a problem connecting to the server. Try again later.",
                icon="🚨",
            )

    st.success(f"Estimated fare is {output}")


if __name__ == "__main__":
    mlflow_uri = os.getenv("MLFLOW_URI")
    mlflow_experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME")

    run(mlflow_uri, mlflow_experiment_name)
