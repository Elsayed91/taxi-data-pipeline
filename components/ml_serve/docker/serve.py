import mlflow.pyfunc
import streamlit as st
import pandas as pd
import numpy as np
from helpers import PredictionAssistant

model_name = "xgboost-fare-predictor"
stage = "Staging"
mlflow.set_tracking_uri(f"http://mlflow-service.default.svc.cluster.local:5000")
model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{stage}")


def run():

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
        df = PredictionAssistant(input_df, "zones.csv").prepare()
        output = model.predict(df)
        output = "$" + str(output)

    st.success(f"The output is {output}")


if __name__ == "__main__":
    run()
