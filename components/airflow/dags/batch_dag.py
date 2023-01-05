import os
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
from parse_state import SparkApplication

# envs={"dag_uri": "{{ dag_run.conf.URI }}"},
KubeResourceKind.register_global_kind(SparkApplication)

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
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL")
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")

    t1 = KubernetesJobOperator(
        task_id="aws_to_gcs",
        body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
        command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
        arguments=[
            "--source",
            "{{ dag_run.conf.uri }}",
            "--destination",
            f'gs://{STAGING_BUCKET}/"{{{{ dag_run.conf.category }}}}"',
            "--creds-file",
            "/etc/aws/aws_creds.json",
            "--filename",
            "{{ dag_run.conf.filename }}",
            "--check-exists",
        ],
        jinja_job_args={
            "image": "google/cloud-sdk:alpine",
            "name": "from-aws-to-gcs",
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

    t1
