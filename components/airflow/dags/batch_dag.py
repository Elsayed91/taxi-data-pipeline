import os

import pendulum
from airflow import DAG

from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
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
    "retries": 0,
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
    CATEGORY = "{{ dag_run.conf.category }}"
    URI = "{{ dag_run.conf.uri }}"
    # t1 = KubernetesJobOperator(
    #     task_id="aws_to_gcs",
    #     body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
    #     command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
    #     arguments=[
    #         "--data-source",
    #         "{{ dag_run.conf.uri }}",
    #         "--destination",
    #         f"gs://{STAGING_BUCKET}/{{{{ dag_run.conf.category }}}}",
    #         "--creds-file",
    #         "/etc/aws/aws_creds.json",
    #         "--check-exists",
    #     ],
    #     jinja_job_args={
    #         "image": "google/cloud-sdk:alpine",
    #         "name": "aws-to-gcs",
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
    #     task_id="data_validation",
    #     body_filepath=f"{TEMPLATES_PATH}/spark_pod_template.yaml",
    #     jinja_job_args={
    #         "project": GOOGLE_CLOUD_PROJECT,
    #         "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
    #         "mainApplicationFile": f"local://{BASE}/data_validation/data_validation.py",
    #         "name": "great-expectations",
    #         "instances": 4,
    #         "gitsync": True,
    #         "nodeSelector": JOBS_NODE_POOL,
    #         "executor_memory": "2048m",
    #         "env": {
    #             "GE_CONFIG_DIR": f"{BASE}/data_validation/config",
    #             "PROJECT": GOOGLE_CLOUD_PROJECT,
    #             "STAGING_BUCKET": STAGING_BUCKET,
    #             "DOCS_BUCKET": os.getenv("DOCS_BUCKET"),
    #             "VALIDATION_THRESHOLD": "10%",
    #         },
    #     },
    # )

    # t3 = KubernetesJobOperator(
    #     task_id="etl-batch",
    #     body_filepath=SPARK_POD_TEMPLATE,
    #     jinja_job_args={
    #         "project": GOOGLE_CLOUD_PROJECT,
    #         "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
    #         "mainApplicationFile": f"local://{BASE}/spark/scripts/batch.py",
    #         "name": "spark-k8s",
    #         "instances": 5,
    #         "gitsync": True,
    #         "nodeSelector": JOBS_NODE_POOL,
    #         "executor_memory": "2048m",
    #         "env": {
    #             "SPARK_BUCKET": os.getenv("SPARK_BUCKET"),
    #             "STAGING_BUCKET": STAGING_BUCKET,
    #         },
    #         "envFrom": [{"type": "configMapRef", "name": "spark-env"}],
    #     },
    # )

    t3 = KubernetesJobOperator(
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
            "RUN_DATE": "{{ dag_run.conf.run_date }}",
        },
    )
    t3  # type: ignore
