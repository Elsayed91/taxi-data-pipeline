"""
A DAG for batch loading data. The DAG is trigged by AWS Lambda which sends over values
that are parsed by airflow conf which are subsequently passed to the operators via jinja
templating. 

- `aws_to_gcs` transfers data from AWS to GCS and uses the pod_template.yaml for its
  resource definition.

- `spark-etl` ingests data from GCS into BigQuery using Spark. It also applies some
  transformations and filters out data into clean & triage data. It uses the
  spark_pod_template.yaml for its resource definition.

- `dbt` runs DBT to update the models that are used for machine learning.

- `train_model` trains an XGBOOST model on data from BigQuery. The model and metrics are
  logged to mlflow.
"""
import os
from datetime import datetime, timedelta
import pendulum
from airflow import DAG
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from addons.parse_state import SparkApplication, Deployment


default_args = {
    "owner": "airflow",
    "start_date": pendulum.yesterday(),
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=60),
    "concurrency": 1,
    "max_active_runs": 1,
    "in_cluster": True,
    "random_name_postfix_length": 2,
    "name_prefix": "",
}


today = datetime.today().strftime("%Y-%m-%d")
module_path = os.path.dirname(__file__)
POD_TEMPALTE = os.path.join(module_path, "templates", "pod_template.yaml")
SPARK_POD_TEMPLATE = os.path.join(module_path, "templates", "spark_pod_template.yaml")

with DAG(
    dag_id="full-refresh",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
    tags=["full-refresh"],
    description="initial load/full refresh data pipeline",
) as dag:
    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    SPARK_JOBS_NODE_POOL = os.getenv("SPARK_JOBS_NODE_POOL")
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")
    TRAINING_NODE_POOL = os.getenv("TRAINING_NODE_POOL")

    # t1 = KubernetesJobOperator(
    #     task_id="aws_to_gcs",
    #     body_filepath=POD_TEMPALTE,
    #     command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
    #     arguments=[
    #         "--data-source",
    #         f"s3://{os.getenv('TARGET_S3_BUCKET')}/trip data/",
    #         "--destination",
    #         f"gs://{STAGING_BUCKET}/yellow",
    #         "--creds-file",
    #         "/etc/aws/aws_creds.json",
    #         "--include-prefixes",
    #         "yellow_tripdata_20",
    #         "--exclude-prefixes",
    #         "yellow_tripdata_2009,yellow_tripdata_2010",
    #         "--check-exists",
    #     ],
    #     jinja_job_args={
    #         "image": "google/cloud-sdk:alpine",
    #         "name": "from-aws-to-gcs",
    #         "gitsync": True,
    #         "nodeSelector": BASE_NODE_POOL,
    #         "volumes": [
    #             {
    #                 "name": "aws-creds",
    #                 "type": "secret",
    #                 "reference": "aws-creds",
    #                 "mountPath": "/etc/aws",
    #             }
    #         ],
    #     },
    # )

    # t2 = KubernetesJobOperator(
    #     task_id="spark-etl",
    #     body_filepath=SPARK_POD_TEMPLATE,
    #     jinja_job_args={
    #         "project": GOOGLE_CLOUD_PROJECT,
    #         "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
    #         "mainApplicationFile": f"local://{BASE}/spark/scripts/initial_load.py",
    #         "name": "spark-k8s-init",
    #         "instances": 7,
    #         "gitsync": True,
    #         "nodeSelector": SPARK_JOBS_NODE_POOL,
    #         "executor_memory": "2G",
    #         "env": {
    #             "CATEGORY": "yellow",
    #             "URI": f"gs://{STAGING_BUCKET}/yellow/*",
    #             "SPARK_BUCKET": os.getenv("SPARK_BUCKET"),
    #         },
    #         "envFrom": [{"type": "configMapRef", "name": "spark-env"}],
    #     },
    # )

    # t3 = KubernetesJobOperator(
    #     task_id="dbt",
    #     body_filepath=POD_TEMPALTE,
    #     command=["/bin/bash", f"{SCRIPTS_PATH}/dbt_run.sh"],
    #     arguments=[
    #         "--deps",
    #         "--seed",
    #         "--commands",
    #         "dbt run --full-refresh",
    #         "--tests",
    #         "--generate-docs",
    #     ],
    #     jinja_job_args={
    #         "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/dbt",
    #         "name": "dbt",
    #         "gitsync": True,
    #         "nodeSelector": BASE_NODE_POOL,
    #         "volumes": [
    #             {
    #                 "name": "gcsfs-creds",
    #                 "type": "secret",
    #                 "reference": "gcsfs-creds",
    #                 "mountPath": "/mnt/secrets",
    #             }
    #         ],
    #         "envFrom": [{"type": "configMapRef", "name": "dbt-env"}],
    #     },
    #     envs={"DBT_PROFILES_DIR": f"{BASE}/dbt/app", "RUN_DATE": today},
    # )

    # t4 = KubernetesJobOperator(
    #     task_id="train_model",
    #     body_filepath=POD_TEMPALTE,
    #     command=["python", f"{BASE}/ml_train/script/train.py"],
    #     jinja_job_args={
    #         "name": "xgb-model-training",
    #         "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/ml_train",
    #         "gitsync": True,
    #         "nodeSelector": TRAINING_NODE_POOL,
    #     },
    #     envs={
    #         "TARGET_DATASET": os.getenv("ML_DATASET"),
    #         "TARGET_TABLE": "dbt__ml__yellow_fare",
    #         "TRACKING_SERVICE": "mlflow-service",
    #         "MLFLOW_EXPERIMENT_NAME": "taxi-fare-prediction-v3",
    #         "TARGET_COLUMN": "fare_amount",
    #         "MLFLOW_BUCKET": os.getenv("MLFLOW_BUCKET"),
    #     },
    # )
    # t5 = KubernetesJobOperator(
    #     task_id="serve_model",
    #     body_filepath=POD_TEMPALTE,
    #     arguments=[
    #         "apply",
    #         "-f" "/git/repo/components/ml_serve/manifests/serving.yaml",
    #     ],
    #     jinja_job_args={
    #         "name": "serve-model",
    #         "image": f"bitnami/kubectl",
    #         "gitsync": True,
    #         "nodeSelector": BASE_NODE_POOL,
    #     },
    # )
    t5 = KubernetesJobOperator(
        task_id="serve_model",
        body_filepath="/git/repo/components/ml_serve/manifests/serving.yaml",
        random_name_postfix_length=0,
    )
    t5
    # t1 >> t2 >> t3 >> t4  # type: ignore
