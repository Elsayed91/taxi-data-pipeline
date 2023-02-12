"""
This module provides definitions for using the Kind: SparkApplication & Deployment with
the KubernetesJobOperator in Apache Airflow. It includes two main functions,
parse_spark_application and parse_deployment, which parse the status of a SparkApplication
and Deployment respectively, and return the state of the resource. The module also
includes two classes, SparkApplication and Deployment, which extend the
KubeApiConfiguration class and are registered as global kinds for the KubeResourceKind.
Reference: https://github.com/LamaAni/KubernetesJobOperator/blob/master/docs/custom_kinds.md
"""
from airflow_kubernetes_job_operator.kube_api import (
    KubeResourceState,
    KubeApiConfiguration,
    KubeResourceKind,
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
    if "status" not in body:
        return KubeResourceState.Pending

    conditions = body["status"].get("conditions", [])
    available_condition = next(
        (c for c in conditions if c["type"] == "Available"), None
    )
    progressing_condition = next(
        (c for c in conditions if c["type"] == "Progressing"), None
    )

    if (
        available_condition is not None
        and available_condition["status"] == "True"
        and progressing_condition is not None
        and progressing_condition["status"] == "True"
    ):
        return KubeResourceState.Succeeded
    elif available_condition is not None and available_condition["status"] == "False":
        return KubeResourceState.Running
    elif (
        progressing_condition is not None and progressing_condition["status"] == "False"
    ):
        return KubeResourceState.Failed
    else:
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

KubeResourceKind.register_global_kind(SparkApplication)
KubeResourceKind.register_global_kind(Deployment)
