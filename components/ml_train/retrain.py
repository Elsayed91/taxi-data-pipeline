import mlflow
import mlflow.xgboost

# Load the XGBoost model from the registry
model = mlflow.xgboost.load_model("xgboost-predictor")

# Fit the model to the training data, using the loaded model as the starting point for training
model.fit(X_train, y_train, xgb_model=model.get_booster())

# Save the updated model to the registry
mlflow.xgboost.save_model(model, "xgboost-predictor")
