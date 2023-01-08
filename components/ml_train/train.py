from xgboost.spark import SparkXGBRegressor
import xgboost as xgb
import datetime
import os
from pyspark.ml.feature import VectorAssembler, VectorIndexer
import mlflow
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.linalg import Vectors
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from xgboost.spark import SparkXGBRegressor
from pyspark.ml import Pipeline
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.ml.evaluation import RegressionEvaluator


model_name = "xgboost-fare-predictor"
target_dataset = os.getenv("TARGET_DATASET")
target_table = os.getenv("TARGET_TABLE")
mlflow_tracking_server = os.getenv("TRACKING_SERVICE", "mlflow-service")
mlflow_experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "taxi-fare-prediction-v2")
target_column = os.getenv("TARGET_COLUMN", "fare_amount")
mlflow_bucket = os.getenv("MLFLOW_BUCKET", "mlflow-cacfcc1b69")


df = load_data(target_dataset, target_table, 50, "percentage")  # type: ignore


target_column = "fare_amount"
feature_names = [x.name for x in df.schema if x.name != target_column]
train_df, test_df = df.randomSplit([0.7, 0.3], seed=0)

vectorAssembler = VectorAssembler(inputCols=feature_names, outputCol="rawFeatures")
vectorIndexer = VectorIndexer(
    inputCol="rawFeatures", outputCol="features", maxCategories=4
)

regressor = SparkXGBRegressor(
    features_col=feature_names,
    label_col=target_column,
    num_workers=2,
)


paramGrid = (
    ParamGridBuilder()
    .addGrid(regressor.max_depth, [2, 5])  # type: ignore
    .addGrid(regressor.n_estimators, [10, 100])  # type: ignore
    .build()
)


evaluator = RegressionEvaluator(
    metricName="rmse",
    labelCol=regressor.getLabelCol(),
    predictionCol=regressor.getPredictionCol(),
)

cv = CrossValidator(
    estimator=regressor, evaluator=evaluator, estimatorParamMaps=paramGrid
)


pipeline = Pipeline(stages=[vectorAssembler, vectorIndexer, cv])

mlflow.set_tracking_uri(
    f"http://{mlflow_tracking_server}.default.svc.cluster.local:5000"
)


mlflow.set_experiment(mlflow_experiment_name)

with mlflow.start_run():
    mlflow.xgboost.autolog()
    pipelineModel = pipeline.fit(train_df)
    predictions = pipelineModel.transform(test_df)
    rmse = evaluator.evaluate(predictions)
    mlflow.log_params({"rmse": rmse})
    logged_model = mlflow.xgboost.log_model(pipeline, model_name)
