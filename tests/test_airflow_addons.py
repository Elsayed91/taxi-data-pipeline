from components.airflow.dags.addons.parse_state import (
    parse_spark_application,
    parse_deployment,
)
from components.lambdafn.main import extract_target_date
from components.airflow.dags.lambda_integration import get_conf
from datetime import datetime

import pytest

from airflow_kubernetes_job_operator.kube_api import KubeResourceState
import os


def test_parse_spark_application():
    # Test a pending state
    body = {}
    assert parse_spark_application(body) == KubeResourceState.Pending

    # Test a running state
    body = {"status": {"applicationState": {"state": "RUNNING"}}}
    assert parse_spark_application(body) == KubeResourceState.Running

    # Test a failed state
    body = {"status": {"applicationState": {"state": "FAILED"}}}
    assert parse_spark_application(body) == KubeResourceState.Failed

    body = {"status": {"applicationState": {"state": "UNKNOWN"}}}
    assert parse_spark_application(body) == KubeResourceState.Failed

    body = {"status": {"applicationState": {"state": "DELETED"}}}
    assert parse_spark_application(body) == KubeResourceState.Failed

    # Test a succeeded state
    body = {"status": {"applicationState": {"state": "COMPLETED"}}}
    assert parse_spark_application(body) == KubeResourceState.Succeeded


def test_parse_deployment():
    # Test a pending state
    body = {}
    assert parse_deployment(body) == KubeResourceState.Pending

    # Test a running state
    body = {
        "status": {
            "conditions": [
                {
                    "type": "Available",
                    "status": "False",
                },
                {
                    "type": "Progressing",
                    "status": "True",
                },
            ],
        },
    }
    assert parse_deployment(body) == KubeResourceState.Running

    # Test a failed state
    body = {
        "status": {
            "conditions": [
                {
                    "type": "Progressing",
                    "status": "False",
                },
            ],
        },
    }
    assert parse_deployment(body) == KubeResourceState.Failed

    # Test a succeeded state
    body = {
        "status": {
            "conditions": [
                {
                    "type": "Available",
                    "status": "True",
                },
                {
                    "type": "Progressing",
                    "status": "True",
                },
            ],
        },
    }
    assert parse_deployment(body) == KubeResourceState.Succeeded


def test_get_run_date():
    # Test with different filename
    assert extract_target_date("green_tripdata_2022-09.parquet") == "2022-09-01"

    # Test with different filename format
    assert extract_target_date("tripdata_2022-10.csv") == "2022-10-01"
    assert extract_target_date("tripdata_2022-10-10.csv") == "2022-10-01"


@pytest.mark.aws_lambda
def test_get_conf(mocker):
    # Create a mock DAG run object
    dag_run = mocker.Mock()

    # Set the mock DAG run's conf attribute to a dictionary
    # containing the URI and file_name keys
    dag_run.conf = {"URI": "x", "FILENAME": "y", "RUN_DATE": "z", "CATEGORY": "w"}
    result = get_conf(
        assertion_result_1="x",
        assertion_result_2="y",
        assertion_result_3="z",
        assertion_result_4="w",
        dag_run=dag_run,
    )

    # Assert that the result is "test successful"
    assert result == "test successful"

    with pytest.raises(
        AssertionError,
        match="dag triggered but have not received correct data, test unsuccessful.",
    ):
        get_conf("a", "b", "z", "w", dag_run=dag_run)

    with pytest.raises(
        AssertionError,
        match="dag triggered but have not received correct data, test unsuccessful.",
    ):
        get_conf("x", "y", "c", "q", dag_run=dag_run)

    dag_run.conf = {}
    with pytest.raises(
        AssertionError, match="dag triggered but conf is empty. review lambda code"
    ):
        get_conf("x", "y", "z", "w", dag_run=dag_run)
