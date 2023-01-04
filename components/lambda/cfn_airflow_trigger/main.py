import os
from tempfile import NamedTemporaryFile

import functions_framework
import googleapiclient.discovery
import kubernetes
import kubernetes.client
from kubernetes.stream import stream


def token():
    credentials = googleapiclient._auth.default_credentials()
    # import google.auth
    # credentials, project_id = google.auth.default(scopes=scopes)
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    scoped = googleapiclient._auth.with_scopes(credentials, scopes)
    googleapiclient._auth.refresh_credentials(scoped)
    return scoped.token


def kubernetes_api(project, cluster_zone, cluster_name):
    name = f"projects/{project}/locations/{cluster_zone}/clusters/{cluster_name}"
    gke_clusters = gke.projects().locations().clusters()
    gke_cluster = gke_clusters.get(name=name).execute()
    config = kubernetes.client.Configuration()
    config.host = f'https://{gke_cluster["endpoint"]}'
    config.api_key_prefix["authorization"] = "Bearer"
    config.api_key["authorization"] = token()
    config.debug = False

    with NamedTemporaryFile(delete=False) as cert:
        cert.write(
            base64.decodebytes(
                gke_cluster["masterAuth"]["clusterCaCertificate"].encode()
            )
        )
        config.ssl_ca_cert = cert.name

    client = kubernetes.client.ApiClient(configuration=config)
    api = kubernetes.client.CoreV1Api(client)
    return api


def trigger_dag(project, cluster_zone, cluster_name, command):
    api = kubernetes_api(project, cluster_zone, cluster_name)
    name = "airflow"  # str | name of the PodExecOptions
    namespace = (
        "default"  # str | object name and auth scope, such as for teams and projects
    )

    command = ["/bin/bash", "-c", command]

    exec_cmd = stream(
        api.connect_post_namespaced_pod_exec(name, namespace, command=command)
    )

    print(exec_cmd)


@functions_framework.cloud_event
def main(cloud_event):

    PROJECT = os.getenv("PROJECT")
    ZONE = os.getenv("GCP_ZONE")
    CLUSTER_NAME = os.getenv("CLUSTER_NAME")
    DAG_NAME = os.getenv("DAG_NAME")
    URI = f"gs://{cloud_event.data['bucket']}/{cloud_event.data['name']}"
    COMMAND_STRING = f"""airflow dags unpause {DAG_NAME} && airflow dags trigger {DAG_NAME} --conf '{{"URI":"{URI}"}}'"""
    trigger_dag(PROJECT, ZONE, CLUSTER_NAME, COMMAND_STRING)
