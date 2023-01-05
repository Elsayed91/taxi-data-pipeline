from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator,
)
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# default_args are the default arguments for the DAG
default_args = {
    "owner": "me",
    "start_date": days_ago(2),
    "depends_on_past": False,
}

# Create a DAG with default_args
with DAG(
    "batch-dag",
    default_args=default_args,
    description="A dummy DAG to demonstrate command line configuration",
    template_searchpath=["/git/repo/components/airflow/dags"],
) as dag:

    import os

    GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    STAGING_BUCKET = os.getenv("STAGING_BUCKET")
    BASE = "/git/repo/components"
    TEMPLATES_PATH = f"{BASE}/airflow/dags/templates"
    SCRIPTS_PATH = f"{BASE}/airflow/dags/scripts"
    JOBS_NODE_POOL = os.getenv("JOBS_NODE_POOL")  # remove z after terraform re
    BASE_NODE_POOL = os.getenv("BASE_NODE_POOL")

    # t4 = KubernetesJobOperator(
    #     task_id="resize",
    #     body_filepath=f"{TEMPLATES_PATH}/pod_template.yaml",
    #     command=["/bin/bash", "-c"],
    #     arguments=["echo", "{{ dag_run.conf.URI }}", "clusters;", "echo $dag_uri"],
    #     jinja_job_args={
    #         "image": "google/cloud-sdk:alpine",
    #         "name": "testi",
    #     },
    #     envs={"dag_uri": "{{ dag_run.conf.URI }}"},
    #     in_cluster=True,
    #     random_name_postfix_length=2,
    #     name_prefix="",
    #     dag=dag,
    # )

    def my_dag_func(**kwargs):
        conf = kwargs["dag_run"].conf
        file_uri = conf["URI"]
        bucket, file_path = file_uri.replace("s3://", "").split("/", 1)
        file_name = file_path.split("/")[-1]
        return bucket, file_path, file_name

    # Create a PythonOperator that calls the print_conf function
    print_conf_task = PythonOperator(
        task_id="print_conf",
        python_callable=my_dag_func,
        provide_context=True,
    )

    task = BashOperator(
        task_id="bash_operator_task",
        bash_command='echo "Bucket: {{ task_instance.xcom_pull(task_ids="print_conf_task", key="bucket") }}, \
        File Path: {{ task_instance.xcom_pull(task_ids="print_conf_task", key="file_path") }}"',
    )
    # Pass in the variables using the `provide_context` parameter
    # provide_context=True

    print_conf_task >> task
# Set the order of the tasks using set_upstream and set_downstream
# print_conf_task

# Specify the command line arguments for the DAG in the form "key=value"
# For example, to pass a configuration called "foo" with value "bar", you can use:
# $ airflow trigger_dag dummy_dag --conf '{"foo":"bar"}'
