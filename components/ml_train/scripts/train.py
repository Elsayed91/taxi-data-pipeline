"""
Module for training and logging XGBoost regression models using scikit-learn and mlflow.
This module includes logic for loading, splitting data, performing grid search
cross-validation, and logging the model's performance, parameters and artifacts.
"""
import logging
import os

import mlflow
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV, train_test_split
from xgboost import XGBRegressor

from train_utils import load_data

logging.basicConfig(level=logging.DEBUG)

# Environmental variables
target_dataset = os.getenv("TARGET_DATASET")
target_table = os.getenv("TARGET_TABLE")
target_column = os.getenv("TARGET_COLUMN")
model_name = os.getenv("MODEL_NAME")
mlflow_bucket = os.getenv("MLFLOW_BUCKET")
mlflow.set_tracking_uri(os.getenv("MLFLOW_URI"))
exp = mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME"))
exp_id = exp.experiment_id

# Load data
df = load_data(target_dataset, target_table)
y = df[target_column]
X = df.drop([target_column], axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1, test_size=0.3)

# Model parameters
param = {
    "max_depth": [6],
    "n_estimators": [ 25, 100],
    "min_child_weight": [3, 5, 7],
}

# Grid search
grid_search = GridSearchCV(
    estimator=XGBRegressor(),
    param_grid=param,
    scoring="neg_mean_squared_error",
    n_jobs=-1,
    verbose=2,
)

# Fit model
xgb_model = grid_search.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)
model = grid_search.best_estimator_

# Log metrics and parameters
with mlflow.start_run(experiment_id=exp_id, run_name="XGBoostRegressor"):
    cv_results = grid_search.cv_results_
    for params, metric, rank in zip(
        cv_results["params"],
        cv_results["mean_test_score"],
        cv_results["rank_test_score"],
    ):
        with mlflow.start_run(experiment_id=exp_id, nested=True):
            mlflow.log_params(params)
            mlflow.log_metric("RMSE", np.sqrt(-metric))
            mlflow.set_tag("rank", rank)

    mlflow.log_params(grid_search.best_params_)
    mlflow.log_metrics({"RMSE": mean_squared_error(y_test, y_pred, squared=False)})
    print("logging model to mlflow")
    mlflow.xgboost.log_model(
        xgb_model=model, artifact_path="xgb-model", registered_model_name=model_name
    )
