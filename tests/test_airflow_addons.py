from components.airflow.dags.addons.parse_state import parse_spark_application
from components.airflow.dags.addons.extract_target_date import extract_target_date

import pytest

from airflow_kubernetes_job_operator.kube_api import KubeResourceState


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


def test_get_run_date():
    # Test with default filename
    assert extract_target_date() == "2022-08-01"

    # Test with different filename
    assert extract_target_date("green_tripdata_2022-09.parquet") == "2022-09-01"

    # Test with different filename format
    assert extract_target_date("tripdata_2022-10.csv") == "2022-10-01"
    assert extract_target_date("tripdata_2022-10-10.csv") == "2022-10-01"
