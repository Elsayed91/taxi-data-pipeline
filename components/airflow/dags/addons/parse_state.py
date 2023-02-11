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
    conditions = body.get("status", {}).get("conditions", [])
    available_condition = next(
        (c for c in conditions if c["type"] == "Available"), None
    )
    progressing_condition = next(
        (c for c in conditions if c["type"] == "Progressing"), None
    )

    if available_condition and available_condition["status"] == "True":
        return KubeResourceState.Succeeded
    if available_condition and available_condition["status"] == "False":
        return KubeResourceState.Failed
    if progressing_condition and progressing_condition["status"] == "True":
        return KubeResourceState.Running
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
