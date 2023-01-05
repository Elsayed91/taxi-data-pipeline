from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "me",
    "start_date": days_ago(2),
    "depends_on_past": False,
}


with DAG(
    "lambda_integration_test",
    default_args=default_args,
    description="A dag that is part of a lambda integration test",
) as dag:

    test_file_uri = "s3://stella-9af1e2ce16/yellow_tripdata_2019-08.parquet"
    test_file_name = "yellow_tripdata_2019-08.parquet"

    def get_conf(assertion_result_1, assertion_result_2, **kwargs):
        """
        Checks that the values of the URI and file_name keys in the DAG
        run configuration are equal to expected values.

        Args:
            **kwargs: Keyword arguments containing the context variables.

        Returns:
            str: "test successful" if the values of URI and file_name meet
            expectations. "dag triggered but have not received correct data,
            test unsuccessful." If conf values are empty it returns "dag
            triggered but conf is empty. test unsuccessful.".
        """
        conf = kwargs["dag_run"].conf
        if not bool(conf):
            return "dag triggered but conf is empty. review lambda code"
        file_uri = conf["URI"]
        filename = conf["file_name"]

        try:
            assert file_uri == assertion_result_1
            assert filename == assertion_result_2
        except AssertionError:
            return (
                "dag triggered but have not received correct data, test unsuccessful."
            )
        else:
            return "test successful"

    assertion_task = PythonOperator(
        task_id="print_conf",
        python_callable=get_conf,
        provide_context=True,
        op_kwargs={
            "assertion_result_1": test_file_uri,
            "assertion_result_2": test_file_name,
        },
    )

    assertion_task  # type: ignore
