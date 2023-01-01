import os
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import (
    SparkKubernetesOperator,
)
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import (
    SparkKubernetesSensor,
)
from airflow.utils.task_group import TaskGroup
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)

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
}

with DAG(
    dag_id="full-refresh",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
    tags=["full-refresh"],
    template_searchpath=["/git/repo/components/airflow/dags"],
) as dag:
    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    POD_TEMPLATE_PATH = f"{BASE}/airflow/dags/template/pod_template.yaml"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL", "jobs")

    t1 = KubernetesJobOperator(
        task_id="aws_to_gcs",
        body_filepath=POD_TEMPLATE_PATH,
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
            "--yellow",
        ],
        jinja_job_args={
            "IMAGE": "google/cloud-sdk:alpine",
            "gitsync": True,
            "nodeSelector": JOBS_NODE_POOL,
            "volumes": [
                {"type": "secret", "name": "aws-creds", "mountPath": "/etc/aws"}
            ],
        },
        in_cluster=True,
        random_name_postfix_length=2,
        name_prefix="",
    )
