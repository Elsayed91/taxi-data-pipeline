"""
This module creates the needed definitions to use Kind: SparkApplication with the
KubernetesJobOperator.
"""
from airflow_kubernetes_job_operator.kube_api import (
    KubeResourceState,
    KubeApiConfiguration,
)


def parse_spark_application(body) -> KubeResourceState:
    FAILURE_STATES = ("FAILED", "UNKNOWN", "DELETED")
    SUCCESS_STATES = ("COMPLETED",)

    if "status" not in body:
        return KubeResourceState.Pending
    application_state = body["status"]["applicationState"]["state"]

    if application_state in FAILURE_STATES:
        return KubeResourceState.Failed
    if application_state in SUCCESS_STATES:
        return KubeResourceState.Succeeded

    return KubeResourceState.Running


def parse_deployment(body) -> KubeResourceState:
    SUCCESS_STATES = ("Available", "Progressing")
    FAILURE_STATES = ("Failed",)
    PENDING_STATES = ("Pending",)

    if "status" not in body:
        return KubeResourceState.Pending

    conditions = body["status"].get("conditions", [])
    for condition in conditions:
        if condition["type"] == "Available":
            if condition["status"] == "True":
                return KubeResourceState.Succeeded
            elif condition["status"] == "False":
                return KubeResourceState.Failed
        elif condition["type"] == "Progressing":
            if condition["status"] == "True":
                return KubeResourceState.Running
            elif condition["status"] == "False":
                return KubeResourceState.Failed

    return KubeResourceState.Pending


Deployment = KubeApiConfiguration.register_kind(
    name="Deployment",
    api_version="apps/v1",
    parse_kind_state=parse_deployment,
)

SparkApplication = KubeApiConfiguration.register_kind(
    name="SparkApplication",
    api_version="sparkoperator.k8s.io/v1beta2",
    parse_kind_state=parse_spark_application,
)
