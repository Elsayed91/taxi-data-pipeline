import mlflow.pyfunc
import streamlit as st
import pandas as pd
import numpy as np


model_name = "xgboost-fare-predictor"
stage = "Staging"

model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{stage}")


def run():

    st.title("New York Taxi Fare Predictor")

    passengers = st.number_input("Passengers", min_value=1, max_value=7, value=1)
    borough_options = df["borough"].unique()
    borough_options = ["All"] + list(borough_options)
    default_ix = borough_options.index("All")
    pickup_borough = st.selectbox("Pickup Borough", borough_options, index=default_ix)
    dropoff_borough = st.selectbox("Dropoff Borough", borough_options, index=default_ix)
    if pickup_borough == "All":
        pickup_zone_options = df["zone"].unique()
    else:
        pickup_zone_options = df[df["borough"] == borough]["zone"].unique()
    pickup_zone = st.selectbox("Pickup Zone", pickup_zone_options)
    if dropoff_borough == "All":
        dropoff_zone_options = df["zone"].unique()
    else:
        dropoff_zone_options = df[df["borough"] == borough]["zone"].unique()
    dropoff_zone = st.selectbox("Dropoff Zone", dropoff_zone_options)
    output = ""

    input_dict = {
        "pickup_zone": pickup_zone,
        "dropoff_zone": dropoff_zone,
        "passengers": passengers,
    }
    input_df = pd.DataFrame([input_dict])

    if st.button("Predict"):
        output = model.predict(data)
        output = "$" + str(output)

    st.success(f"The output is {output}")


if __name__ == "__main__":
    run()
