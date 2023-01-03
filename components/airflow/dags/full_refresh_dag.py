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

from airflow_kubernetes_job_operator.kube_api import KubeResourceState


def parse_spark_application(body) -> KubeResourceState:
    if "status" not in body:
        return KubeResourceState.Pending

    status = body["status"]
    if "completionTime" in status:
        return KubeResourceState.Succeeded
    if "failed" in status:
        return KubeResourceState.Failed
    if "deletionTimestamp" in body:
        return KubeResourceState.Deleted
    return KubeResourceState.Running


from airflow_kubernetes_job_operator.kube_api import (
    KubeApiConfiguration,
    KubeResourceKind,
)

SparkApplication = KubeApiConfiguration.register_kind(
    name="SparkApplication",
    api_version="sparkoperator.k8s.io/v1beta2",
    parse_kind_state=parse_spark_application,
)

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
    POD_TEMPLATE_PATH = f"{BASE}/airflow/dags/templates/pod_template.yaml"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL", "jobs")

    t1 = KubernetesJobOperator(
        task_id="test",
        body_filepath=f"{BASE}/airflow/dags/templates/spark_pod_template.yaml",
        jinja_job_args={
            "project": GOOGLE_CLOUD_PROJECT,
            "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
            "mainApplicationFile": f"local://{BASE}/spark/scripts/fix_schema.py",
            "name": "spark-k8s-init",
            "instances": 4,
            "gitsync": True,
            "nodeSelector": JOBS_NODE_POOL,
            "env": {
                "URI": f"gs://{STAGING_BUCKET}/yellow/*",
                "NAME_PREFIX": "yellow_tripdata_",
            },
        },
    )

    # t1 = KubernetesJobOperator(
    #     task_id="aws_to_gcs",
    #     body_filepath=POD_TEMPLATE_PATH,
    #     command=["/bin/bash", f"{SCRIPTS_PATH}/aws_gcloud_data_transfer.sh"],
    #     arguments=[
    #         "--source-bucket",
    #         f"s3://{os.getenv('TARGET_S3_BUCKET')}/trip data/",
    #         "--target-bucket",
    #         f"gs://{STAGING_BUCKET}",
    #         "--project",
    #         f"{GOOGLE_CLOUD_PROJECT}",
    #         "--creds-file",
    #         "/etc/aws/aws_creds.json",
    #         "--include-prefixes",
    #         "yellow_tripdata_20",
    #         "--exclude-prefixes",
    #         "yellow_tripdata_2009,yellow_tripdata_2010",
    #         "--check-exists",
    #         "--",
    #         "yellow",
    #     ],
    #     jinja_job_args={
    #         "image": "google/cloud-sdk:alpine",
    #         "name": "from-aws-to-gcs",
    #         "gitsync": True,
    #         "nodeSelector": JOBS_NODE_POOL,
    #         "volumes": [
    #             {
    #                 "name": "aws-creds",
    #                 "type": "secret",
    #                 "reference": "aws-creds",
    #                 "mountPath": "/etc/aws",
    #             }
    #         ],
    #     },
    #     in_cluster=True,
    #     random_name_postfix_length=2,
    #     name_prefix="",
    # )

    # with TaskGroup(group_id="spark-init-etl") as tg1:
    #     tg1_1 = SparkKubernetesOperator(
    #         task_id="spark-etl",
    #         namespace="default",
    #         application_file=f"templates/spark_pod_template.yaml",
    # params={
    #     "project": GOOGLE_CLOUD_PROJECT,
    #     "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/spark",
    #     "mainApplicationFile": f"local://{BASE}/spark/scripts/fix_schema.py",
    #     "name": "spark-k8s-init",
    #     "instances": 4,
    #     "gitsync": True,
    #     "nodeSelector": JOBS_NODE_POOL,
    #     "env": {
    #         "URI": f"gs://{STAGING_BUCKET}/yellow/*",
    #         "NAME_PREFIX": "yellow_tripdata_",
    #     },
    #         },
    #     )

    #     tg1_2 = SparkKubernetesSensor(
    #         task_id="spark-etl-monitor",
    #         application_name="{{ task_instance.xcom_pull(task_ids='spark-init-etl.spark-etl') ['metadata']['name'] }}",
    #         attach_log=True,
    #     )
    #     tg1_1 >> tg1_2  # type: ignore

    t1  # type: ignore
