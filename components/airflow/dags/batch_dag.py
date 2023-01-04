from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# default_args are the default arguments for the DAG
default_args = {
    "owner": "me",
    "start_date": days_ago(2),
    "depends_on_past": False,
}

# Create a DAG with default_args
dag = DAG(
    "batch-dag",
    default_args=default_args,
    description="A dummy DAG to demonstrate command line configuration",
)

t = "{{ dag_run.conf.URI }}"
# Define a function that prints the command line configuration
def print_conf():
    print(f"the value of uri is {t}")
    return t


# Create a PythonOperator that calls the print_conf function
print_conf_task = PythonOperator(
    task_id="print_conf",
    python_callable=print_conf,
    provide_context=True,
    dag=dag,
)

# Set the order of the tasks using set_upstream and set_downstream
print_conf_task

# Specify the command line arguments for the DAG in the form "key=value"
# For example, to pass a configuration called "foo" with value "bar", you can use:
# $ airflow trigger_dag dummy_dag --conf '{"foo":"bar"}'
