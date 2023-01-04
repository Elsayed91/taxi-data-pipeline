from airflow import DAG
import os
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)

# default_args are the default arguments for the DAG
default_args = {
    "owner": "me",
    "start_date": days_ago(2),
    "depends_on_past": False,
}

# Create a DAG with default_args
with DAG(
    dag_id="batch-dag",
    schedule_interval=None,
    default_args=default_args,
    catchup=False,
    tags=["batch-dag"],
    template_searchpath=["/git/repo/components/airflow/dags"],
) as dag:
    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    TEMPLATES_PATH = f"{BASE}/airflow/dags/templates"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL")  # remove z after terraform re
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")

    t4 = KubernetesJobOperator(
        task_id="resize",
        body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
        command=["/bin/bash", "-c"],
        arguments=["echo", "{{ dag_run.conf.URI }}", "clusters;", "echo $dag_uri"],
        jinja_job_args={
            "image": "google/cloud-sdk:alpine",
            "name": "testi",
        },
        envs={"dag_uri": "{{ dag_run.conf.URI }}"},
        in_cluster=True,
        random_name_postfix_length=2,
        name_prefix="",
    )
# Define a function that prints the command line configuration
# def print_conf(**kwargs):
#     conf = kwargs["dag_run"].conf
#     if conf:
#         print(f"Configuration received: {conf}")
#     else:
#         print("No configuration received")


# # Create a PythonOperator that calls the print_conf function
# print_conf_task = PythonOperator(
#     task_id="print_conf",
#     python_callable=print_conf,
#     provide_context=True,
#     dag=dag,
# )

# Set the order of the tasks using set_upstream and set_downstream
print_conf_task

# Specify the command line arguments for the DAG in the form "key=value"
# For example, to pass a configuration called "foo" with value "bar", you can use:
# $ airflow trigger_dag dummy_dag --conf '{"foo":"bar"}'
