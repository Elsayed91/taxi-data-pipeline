import os
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
from dags.addons.parse_state import SparkApplication

KubeResourceKind.register_global_kind(SparkApplication)


today = datetime.today().strftime("%Y-%m-%d")

import logging

logging.basicConfig(level=logging.DEBUG)

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


with DAG(
    dag_id="full-refresh",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
    tags=["full-refresh"],
    description="initial load/full refresh data pipeline",
    template_searchpath=["/git/repo/components/airflow/dags"],
) as dag:
    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    TEMPLATES_PATH = f"{BASE}/airflow/dags/templates"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL")
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")
    t1 = KubernetesJobOperator(
        task_id="aws_to_gcs",
        body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
        command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
        arguments=[
            "--source-bucket",
            f"s3://{os.getenv('TARGET_S3_BUCKET')}/trip data/",
            "--target-bucket",
            f"gs://{STAGING_BUCKET}",
            "--project",
            f"{GOOGLE_CLOUD_PROJECT}",
            "--creds-file",
            "/etc/aws/aws_creds.json",
            "--include-prefixes",
            "yellow_tripdata_20",
            "--exclude-prefixes",
            "yellow_tripdata_2009,yellow_tripdata_2010",
            "--check-exists",
            "--",
            "yellow",
        ],
        jinja_job_args={
            "image": "google/cloud-sdk:alpine",
            "name": "from-aws-to-gcs",
            "gitsync": True,
            "nodeSelector": JOBS_NODE_POOL,
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
        task_id="test",
        body_filepath=f"{TEMPLATES_PATH}/spark_pod_template.yaml",
        jinja_job_args={
            "project": GOOGLE_CLOUD_PROJECT,
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
            "mainApplicationFile": f"local://{BASE}/spark/scripts/main_init.py",
            "name": "spark-k8s-init",
            "instances": 7,
            "gitsync": True,
            "nodeSelector": "base",
            "executor_memory": "2048m",
            "env": {
                "CATEGORY": "yellow",
                "URI": f"gs://{STAGING_BUCKET}/yellow/*",
                "SPARK_BUCKET": os.getenv("SPARK_BUCKET"),
                "HISTORICAL_TARGET": f"{os.getenv('HISTORICAL_DATASET')}.{os.getenv('HISTORICAL_TABLE')}",
                "STAGING_TARGET": f"{os.getenv('STAGING_DATASET')}.{os.getenv('YELLOW_STAGING_TABLE')}",
                "TRIAGE_TAREGET": f"{os.getenv('TRIAGE_DATASET')}.{os.getenv('YELLOW_TRIAGE_TABLE')}",
            },
        },
    )

    t3 = KubernetesJobOperator(
        task_id="dbt",
        body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
        command=["/bin/bash", f"{SCRIPTS_PATH}/dbt_run.sh"],
        arguments=[
            "--deps",
            "--seed",
            "--commands",
            "dbt run --full-refresh",
            "--tests" "--generate-docs",
        ],
        jinja_job_args={
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/dbt",
            "name": "dbt",
            "gitsync": True,
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
        envs={"DBT_PROFILES_DIR": f"{BASE}/dbt/app", "RUN_DATE": today},
    )

    t4 = KubernetesJobOperator(
        task_id="resize",
        body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
        command=["/bin/bash", "-c"],
        arguments=[
            "gcloud",
            "container",
            "clusters",
            "resize",
            f"{GKE_CLUSTER_NAME}",
            "--node-pool",
            f"{JOBS_NODE_POOL}",
            "--num-nodes",
            "0",
            "-q",
        ],
        jinja_job_args={
            "image": "google/cloud-sdk:alpine",
            "name": "resize-cluster",
            "nodeSelector": BASE_NODE_POOL,
        },
        in_cluster=True,
        random_name_postfix_length=2,
        name_prefix="",
    )

    t1 >> t2 >> t3
