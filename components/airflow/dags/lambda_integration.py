"""
This module is a part of a lambda function integration test. It consists of a
PythonOperator that uses a function called get_conf.
The purpose of the get_conf function is to verify that the values of the "URI",
"FILENAME", "RUN_DATE", and "CATEGORY" keys in the DAG run configuration are equal to the
expected values. If the values are empty, it raises an AssertionError with an appropriate
message. If the values match the expected values, it returns "test successful".
"""

import logging

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

default_args = {
    "owner": "airflow",
    "start_date": pendulum.yesterday(),
    "depends_on_past": False,
    "retries": 2,
    "concurrency": 1,
    "max_active_runs": 1,
    "in_cluster": True,
    "random_name_postfix_length": 2,
    "name_prefix": "",
}


with DAG(
    "lambda_integration_test",
    default_args=default_args,
    description="A dag that is part of a lambda integration test",
) as dag:

    def get_conf(
        assertion_result_1,
        assertion_result_2,
        assertion_result_3,
        assertion_result_4,
        **kwargs,
    ):
        """
        Checks that the values of the URI, filename, run_date and category keys in
        the DAG run configuration are equal to expected values.

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
            raise AssertionError("dag triggered but conf is empty. review lambda code")

        try:
            file_uri = conf["URI"]
            filename = conf["FILENAME"]
            run_date = conf["RUN_DATE"]
            category = conf["CATEGORY"]
            logger.info(
                f"uri is {file_uri}, and file is {filename} \
                and run_date is {run_date}"
            )
            assert file_uri == assertion_result_1
            assert filename == assertion_result_2
            assert run_date == assertion_result_3
            assert category == assertion_result_4
        except AssertionError:
            raise AssertionError(
                "dag triggered but have not received correct data, test unsuccessful."
            )
        else:
            return "test successful"

    assertion_task = PythonOperator(
        task_id="print_conf",
        python_callable=get_conf,
        provide_context=True,
        op_kwargs={
            "assertion_result_1": f"s3://test-bucket/yellow_tripdata_2019-08.parquet",
            "assertion_result_2": "yellow_tripdata_2019-08.parquet",
            "assertion_result_3": "2019-08-01",
            "assertion_result_4": "yellow",
        },
    )

    assertion_task  # type: ignore
