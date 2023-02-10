from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV
import mlflow
import os
from helpers import *
import logging


logging.basicConfig(level=logging.DEBUG)
# http://michael-harmon.com/blog/GreenBuildings3.html


# define environmental variables
target_dataset = os.getenv("TARGET_DATASET")
target_table = os.getenv("TARGET_TABLE")
mlflow_tracking_server = os.getenv("TRACKING_SERVICE", "mlflow-service")
mlflow.set_tracking_uri(
    f"http://{mlflow_tracking_server}.default.svc.cluster.local:5000"
)
mlflow_experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "taxi-fare-prediction-v2")
target_column = os.getenv("TARGET_COLUMN", "fare_amount")
mlflow_bucket = os.getenv("MLFLOW_BUCKET", "mlflow-cacfcc1b69")
cross_validations = int(os.getenv("CROSS_VALIDATIONS", 1))  # type: ignore
model_name = os.getenv("MODEL_NAME", "xgboost-fare-predictor")


exp = mlflow.set_experiment(mlflow_experiment_name)
exp_id = exp.experiment_id
df = load_data(target_dataset, target_table)  # type: ignore
print(f"df shape is {df.shape}")
y = df[target_column]
X = df.drop([target_column], axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1, test_size=0.3)

param = {
    "max_depth": [2, 4, 6],
    "n_estimators": [15, 25, 100],
    "min_child_weight": [3, 5, 7],
}


print("using grid search")
grid_search = GridSearchCV(
    estimator=XGBRegressor(),
    param_grid=param,
    scoring="neg_mean_squared_error",
    n_jobs=-1,
    verbose=2,
)

print("fitting model")
xgb_model = grid_search.fit(X_train, y_train)
y_pred = xgb_model.predict(X_test)
model = grid_search.best_estimator_
print(model)
with mlflow.start_run(experiment_id=exp_id, run_name="XGBoostRegressor", nested=True):

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

    mlflow.xgboost.log_model(
        xgb_model=model, artifact_path="xgb-model", registered_model_name=model_name
    )
