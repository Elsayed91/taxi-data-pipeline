from airflow_kubernetes_job_operator.kube_api import (
    KubeResourceState,
    KubeApiConfiguration,
)
from airflow_kubernetes_job_operator.kubernetes_job_operator import (
    KubernetesJobOperator as _KubernetesJobOperator,
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


SparkApplication = KubeApiConfiguration.register_kind(
    name="SparkApplication",
    api_version="sparkoperator.k8s.io/v1beta2",
    parse_kind_state=parse_spark_application,
)


class KJO(_KubernetesJobOperator):
    template_fields = list(_KubernetesJobOperator.template_fields)
    template_fields.append("jinja_job_args")
