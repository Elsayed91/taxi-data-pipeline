"""
A DAG for batch loading data. The DAG is trigged by AWS Lambda which sends over values
that are parsed by airflow conf which are subsequently passed to the operators via jinja
templating. 

- `aws_to_gcs` transfers data from AWS to GCS and uses the pod_template.yaml for its
  resource definition.

- `data_validation` runs a Great Expectations data validation job using Spark. It uses the
  spark_pod_template.yaml for its resource definition. the threshold value is defined in
  the environmental variables and can be used to fail the pipeline if data validation is
  lower than the threshold.

- `etl-batch` ingests data from GCS into BigQuery using a Spark application. It also
  applies some transformations and filters out data into clean & triage data. It uses the
  spark_pod_template.yaml for its resource definition.

- `dbt` runs DBT to update the models that are used for machine learning.
"""

import os
import sys

import pendulum
from airflow import DAG
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from addons.parse_state import SparkApplication

KubeResourceKind.register_global_kind(SparkApplication)

import logging

logging.basicConfig(level=logging.DEBUG)
module_path = os.path.dirname(__file__)
POD_TEMPALTE = os.path.join(module_path, "templates", "pod_template.yaml")
SPARK_POD_TEMPLATE = os.path.join(module_path, "templates", "spark_pod_template.yaml")


default_args = {
    "owner": "airflow",
    "start_date": pendulum.yesterday(),
    "depends_on_past": False,
    "retries": 2,
    "concurrency": 1,
    "max_active_runs": 1,
    "in_cluster": True,
    "random_name_postfix_length": 2,
    "name_prefix": "",
}


with DAG(
    dag_id="batch-dag",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    description="batch data pipeline",
) as dag:
    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    TEMPLATES_PATH = f"{BASE}/airflow/dags/templates"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    SPARK_JOBS_NODE_POOL = os.getenv("SPARK_JOBS_NODE_POOL")
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")
    TRAINING_NODE_POOL = os.getenv("TRAINING_NODE_POOL")
    t1 = KubernetesJobOperator(
        task_id="aws_to_gcs",
        body_filepath=POD_TEMPALTE,
        command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
        arguments=[
            "--data-source",
            "{{ dag_run.conf.URI }}",
            "--destination",
            f"gs://{STAGING_BUCKET}/{{{{ dag_run.conf.CATEGORY }}}}",
            "--creds-file",
            "/etc/aws/aws_creds.json",
            "--check-exists",
        ],
        jinja_job_args={
            "image": "google/cloud-sdk:alpine",
            "name": "aws-to-gcs",
            "gitsync": True,
            "nodeSelector": BASE_NODE_POOL,
            "volumes": [
                {
                    "name": "aws-creds",
                    "type": "secret",
                    "reference": "aws-creds",
                    "mountPath": "/etc/aws",
                }
            ],
        },
    )

    t2 = KubernetesJobOperator(
        task_id="data_validation",
        body_filepath=SPARK_POD_TEMPLATE,
        jinja_job_args={
            "project": GOOGLE_CLOUD_PROJECT,
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
            "mainApplicationFile": f"local://{BASE}/data_validation/data_validation.py",
            "name": "great-expectations",
            "instances": 4,
            "gitsync": True,
            "nodeSelector": SPARK_JOBS_NODE_POOL,
            "executor_memory": "2048m",
            "env": {
                "GE_CONFIG_DIR": f"{BASE}/data_validation/config",
                "PROJECT": GOOGLE_CLOUD_PROJECT,
                "STAGING_BUCKET": STAGING_BUCKET,
                "DOCS_BUCKET": os.getenv("DOCS_BUCKET"),
                "VALIDATION_THRESHOLD": "10%",
            },
        },
    )

    t3 = KubernetesJobOperator(
        task_id="etl-batch",
        body_filepath=SPARK_POD_TEMPLATE,
        jinja_job_args={
            "project": GOOGLE_CLOUD_PROJECT,
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
            "mainApplicationFile": f"local://{BASE}/spark/scripts/batch.py",
            "name": "spark-k8s",
            "instances": 5,
            "gitsync": True,
            "nodeSelector": SPARK_JOBS_NODE_POOL,
            "executor_memory": "2048m",
            "env": {
                "SPARK_BUCKET": os.getenv("SPARK_BUCKET"),
                "STAGING_BUCKET": STAGING_BUCKET,
            },
            "envFrom": [{"type": "configMapRef", "name": "spark-env"}],
        },
    )

    t4 = KubernetesJobOperator(
        task_id="dbt",
        body_filepath=POD_TEMPALTE,
        command=["/bin/bash", f"{SCRIPTS_PATH}/dbt_run.sh"],
        arguments=[
            "--deps",
            "--seed",
            "--commands",
            "dbt run",
            "--generate-docs",
        ],
        jinja_job_args={
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/dbt",
            "name": "dbt",
            "gitsync": True,
            "nodeSelector": BASE_NODE_POOL,
            "volumes": [
                {
                    "name": "gcsfs-creds",
                    "type": "secret",
                    "reference": "gcsfs-creds",
                    "mountPath": "/mnt/secrets",
                }
            ],
            "envFrom": [{"type": "configMapRef", "name": "dbt-env"}],
        },
        envs={
            "DBT_PROFILES_DIR": f"{BASE}/dbt/app",
            "RUN_DATE": "{{ dag_run.conf.RUN_DATE }}",
        },
    )

    t5 = KubernetesJobOperator(
        task_id="retrain_model",
        body_filepath=POD_TEMPALTE,
        command=["python", f"{BASE}/ml_train/scripts/train.py"],
        jinja_job_args={
            "name": "xgb-model-training",
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/ml_train",
            "gitsync": True,
            "nodeSelector": TRAINING_NODE_POOL,
        },
        envs={
            "TARGET_DATASET": os.getenv("ML_DATASET"),
            "TARGET_TABLE": "dbt__ml__yellow_fare",
            "TRACKING_SERVICE": "mlflow-service",
            "MLFLOW_EXPERIMENT_NAME": "taxi-fare-prediction-v3",
            "TARGET_COLUMN": "fare_amount",
            "MLFLOW_BUCKET": os.getenv("MLFLOW_BUCKET"),
        },
    )

    t6 = KubernetesJobOperator(
        task_id="refresh_streamlit",
        body_filepath=POD_TEMPALTE,
        arguments=["rollout", "restart", "deployment", "ml_serve"],
        jinja_job_args={
            "name": "refresh-streamlit-model",
            "image": f"bitnami/kubectl",
            "nodeSelector": BASE_NODE_POOL,
        },
    )
    t1 >> t2 >> t3 >> t4 >> t5 >> t6  # type: ignore
