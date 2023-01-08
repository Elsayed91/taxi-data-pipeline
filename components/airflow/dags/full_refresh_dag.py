import os
from datetime import datetime, timedelta
import pendulum
from airflow import DAG
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow_kubernetes_job_operator.kube_api import KubeResourceKind
from addons.parse_state import SparkApplication


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

KubeResourceKind.register_global_kind(SparkApplication)
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
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL")
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")

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
    HISTORICAL_TARGET = (
        f"{os.getenv('HISTORICAL_DATASET')}.{os.getenv('HISTORICAL_TABLE')}"
    )
    STAGING_TARGET = (
        f"{os.getenv('STAGING_DATASET')}.{os.getenv('YELLOW_STAGING_TABLE')}"
    )
    TRIAGE_TARGET = f"{os.getenv('TRIAGE_DATASET')}.init_3_months"

    t2 = KubernetesJobOperator(
        task_id="etl",
        body_filepath=SPARK_POD_TEMPLATE,
        jinja_job_args={
            "project": GOOGLE_CLOUD_PROJECT,
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
            "mainApplicationFile": f"local://{BASE}/spark/scripts/initial_load.py",
            "name": "spark-k8s-init",
            "instances": 7,
            "gitsync": True,
            "nodeSelector": "base",
            "executor_memory": "2048m",
            "env": {
                "CATEGORY": "yellow",
                "URI": f"gs://{STAGING_BUCKET}/yellow/*",
                "SPARK_BUCKET": os.getenv("SPARK_BUCKET"),
                "HISTORICAL_TARGET": HISTORICAL_TARGET,
                "STAGING_TARGET": STAGING_TARGET,
                "TRIAGE_TAREGET": TRIAGE_TARGET,
            },
        },
    )

    t3 = KubernetesJobOperator(
        task_id="dbt",
        body_filepath=POD_TEMPALTE,
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

    t2 >> t3  # type: ignore
    # t1 >> t2 >> t3  # type: ignore
