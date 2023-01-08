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

# http://michael-harmon.com/blog/GreenBuildings3.html

if __name__ == "__main__":
    # define environmental variables
    target_dataset = os.getenv("TARGET_DATASET")
    target_table = os.getenv("TARGET_TABLE")
    mlflow_tracking_server = os.getenv("TRACKING_SERVICE", "mlflow-service")
    mlflow_experiment_name = os.getenv(
        "MLFLOW_EXPERIMENT_NAME", "taxi-fare-prediction-v2"
    )
    target_column = os.getenv("TARGET_COLUMN", "fare_amount")
    mlflow_bucket = os.getenv("MLFLOW_BUCKET", "mlflow-cacfcc1b69")
    cross_validations = int(os.getenv("CROSS_VALIDATIONS", 1))  # type: ignore
    # setup mlflow

    model_name = "xgboost-fare-predictor"

    exp = mlflow.set_experiment(mlflow_experiment_name)
    exp_id = exp.experiment_id

    df = load_data(target_dataset, target_table, 50)  # type: ignore

    y = df[target_column]
    X = df.drop([target_column], axis=1)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=1, test_size=0.3
    )

    # param = {
    #     "max_depth": [2, 4, 6],
    #     "n_estimators": [10, 15, 25, 50, 100, 500],
    #     "colsample_bytree": [0.2, 0.6, 0.8],
    #     "min_child_weight": [3, 5, 7],
    #     "gamma": [0.3, 0.5, 0.7],
    #     "subsample": [0.4, 0.6, 0.8],
    #     "loss": ["ls", "lad"],
    # }

    param = {
        "max_depth": [2, 4],
        "n_estimators": [10, 15],
    }

    grid_search = GridSearchCV(
        estimator=XGBRegressor(),
        param_grid=param,
        scoring="rmse",
        cv=cross_validations,
        n_jobs=-1,
    )

    xgb_model = grid_search.fit(X_train, y_train)
    y_pred = xgb_model.predict(X_test)
    model = grid_search.best_estimator_
    with mlflow.start_run(
        experiment_id=exp_id, run_name="XGBoostRegressor", nested=True
    ):

        cv_results = grid_search.cv_results_

        # loop over each of the parameters and log them along
        # with the metric and rank of the model
        for params, metric, rank in zip(
            cv_results["params"],
            cv_results["mean_test_score"],
            cv_results["rank_test_score"],
        ):

            with mlflow.start_run(experiment_id=exp_id, nested=True):
                # log the parameters
                mlflow.log_params(params)

                # log the R2 score
                mlflow.log_metric("RMSE", metric)

                # set the rank
                mlflow.set_tag("rank", rank)

        # For the best estimator (xbg_model)
        # let's log the parameters for the best model and
        # its metric artifacts
        mlflow.log_params(grid_search.best_params_)
        mlflow.log_metrics({"RMSE": mean_squared_error(y_test, y_pred, squared=False)})

        mlflow.xgboost.log_model(model_name, model)
