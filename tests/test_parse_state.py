from components.airflow.dags.addons.parse_state import parse_spark_application


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
