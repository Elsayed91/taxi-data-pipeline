import bentoml
from bentoml.io import JSON

model_name = "xgboost-fare-predictor"

model_ref = bentoml.xgboost.get(model_name)
# prediction_assistant = model_ref.custom_objects["prediction_assistant"]

model_runner = model_ref.to_runner()
svc = bentoml.Service("ny_taxi_fare_predictor", runners=[model_runner])


@svc.api(input=JSON(), output=JSON())
def predict(data):
    print(model_runner)
    # data = prediction_assistant(data).run()
    prediction = model_runner.predict.run(data)  # type: ignore
    print(prediction)
    result = prediction[0]
    return {"predicted_fare": result}
