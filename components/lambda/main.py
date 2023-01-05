"""
Functionality:
-   The function is triggered when an object is added to an S3 bucket. It retrieves the bucket name and
    object key from the event data, constructs an object URI in the format "s3://bucket_name/key".
-   retrieves variables data (cluster data, DAG name, and namespace) from environment variables.
-   authenticates with Google Cloud Platform (GCP) using a service account key, and uses the Google 
    Kubernetes Engine (GKE) API to retrieve information about a specific cluster and create a 
    Kubernetes client configuration and subsequently a Kubernetes API client.
-   retrieves a list of pods in the specified namespace, and searches for a pod with a name containing 
    "airflow". This is done as the airflow pod unlike the deployment, is usually suffixed randomly.
    If found, it uses the Kubernetes API to execute the command string on the pod to trigger a dag.
    
Best Practices:
    Security:
        1. Using environment variables for sensitive information such as API keys, project names, and bucket names.
        2. Using a temporary file to store the GKE cluster certificate instead of storing it in a variable, 
            preventing it from being exposed in memory.
        3. using SecretsManager to handle sensitive files like the GCP Service Key
        4. Using the NamedTemporaryFile context manager to create a temporary file, which automatically deletes the
    file after it is closed.
    Code Organization:
        1. Code is broken up into small functions each with single responsibility.
        2. 
    Testing: 
        Integration test in the tests folder
    Error Handling:
    

References:
    GKE Authentication: https://stackoverflow.com/questions/54410410/authenticating-to-gke-master-in-python
"""
import os
from tempfile import NamedTemporaryFile
import kubernetes.client
import base64
import googleapiclient.discovery
import kubernetes
from kubernetes.stream import stream
import urllib.parse
from google.oauth2.service_account import Credentials
from aws_lambda_typing.context import Context as LambdaContext
import boto3
from botocore.exceptions import ClientError
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_credentials(secret_id: str = "gcp_key") -> Credentials:
    """
    Retrieves GCP service account credentials from AWS Secrets Manager.

    Args:
        secret_id (str): The ID of the secret in Secrets Manager. Defaults to "gcp_key".

    Returns:
        Credentials: The service account credentials.
    """
    secrets_manager_client = boto3.client("secretsmanager")
    try:
        get_secret_value_response = secrets_manager_client.get_secret_value(
            SecretId=secret_id
        )
    except ClientError as e:
        raise ValueError(f"Unable to retrieve secret '{secret_id}': {e}")
    else:
        service_account_info = json.loads(get_secret_value_response["SecretString"])
        return Credentials.from_service_account_info(service_account_info)


def token(credentials, *scopes):
    scopes = [f"https://www.googleapis.com/auth/{s}" for s in scopes]
    scoped = googleapiclient._auth.with_scopes(credentials, scopes)  # type: ignore
    googleapiclient._auth.refresh_credentials(scoped)  # type: ignore


def get_cluster_info(project, zone, cluster_name, credentials):
    cluster_attributes = f"projects/{project}/locations/{zone}/clusters/{cluster_name}"
    gke = googleapiclient.discovery.build("container", "v1", credentials=credentials)
    gke_clusters = gke.projects().locations().clusters()
    gke_cluster = gke_clusters.get(name=cluster_attributes).execute()
    return gke_cluster


def kubernetes_api(cluster, api_auth_token):
    config = kubernetes.client.Configuration()
    config.host = f'https://{cluster["endpoint"]}'
    config.api_key_prefix["authorization"] = "Bearer"
    config.api_key["authorization"] = api_auth_token
    config.debug = True

    with NamedTemporaryFile(delete=False) as cert:
        cert.write(
            base64.decodebytes(cluster["masterAuth"]["clusterCaCertificate"].encode())
        )
        config.ssl_ca_cert = cert.name  # type: ignore

    client = kubernetes.client.ApiClient(configuration=config)
    api = kubernetes.client.CoreV1Api(client)

    return api


def lambda_handler(event: dict, context: LambdaContext) -> None:

    # variables
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    object_uri = f"s3://{bucket_name}/{key}"
    target_pod_substring = os.getenv("TARGET_POD", "airflow")
    target_container = os.getenv("TARGET_CONTAINER", "scheduler")
    # key = urllib.parse.unquote_plus(
    #     event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    # )
    target_namespace = os.getenv("TARGET_NAMESPACE")
    dag_trigger_command = f"""airflow dags unpause {os.getenv("DAG_NAME")} && airflow dags trigger {os.getenv("DAG_NAME")} --conf '{{"URI":"{object_uri}", "filename":"{key}"}}'"""
    gcp_project = os.getenv("PROJECT")
    gcp_zone = os.getenv("GCP_ZONE")
    gke_name = os.getenv("GKE_CLUSTER_NAME")
    credentials = get_credentials()
    api_auth_token = token(credentials, "cloud-platform")
    # gke_cluster = get_cluster_info(gcp_project, gcp_zone, gke_name, credentials)

    # api = kubernetes_api(gke_cluster, api_auth_token)
    # print(api.list_pod_for_all_namespaces())
    # pods = api.list_namespaced_pod(namespace=str(target_namespace))
    # target_pod = None
    # for pod in pods.items:
    #     if pod.metadata.name.find(target_pod_substring) != -1:
    #         target_pod = pod.metadata.name
    #         break
    # if target_pod:
    #     exec_command = ["/bin/sh", "-c", dag_trigger_command]
    #     resp = stream(
    #         api.connect_get_namespaced_pod_exec,
    #         name=target_pod,
    #         namespace=target_namespace,
    #         container=target_container,
    #         command=exec_command,
    #         stderr=True,
    #         stdin=False,
    #         stdout=True,
    #         tty=False,
    #     )
    #     print("Response: " + resp)
    # credentials = service_account.Credentials.from_service_account_file(
    #     "lambda_key.json"
    # )
    cluster_name = f'projects/{os.getenv("PROJECT")}/locations/{os.getenv("GCP_ZONE")}/clusters/{os.getenv("GKE_CLUSTER_NAME")}'
    gke = googleapiclient.discovery.build("container", "v1", credentials=credentials)
    gke_clusters = gke.projects().locations().clusters()
    gke_cluster = gke_clusters.get(name=cluster_name).execute()
    config = kubernetes.client.Configuration()
    config.host = f'https://{gke_cluster["endpoint"]}'
    config.api_key_prefix["authorization"] = "Bearer"
    config.api_key["authorization"] = api_auth_token
    config.debug = False
    with NamedTemporaryFile(delete=False) as cert:
        cert.write(
            base64.decodebytes(
                gke_cluster["masterAuth"]["clusterCaCertificate"].encode()
            )
        )
        config.ssl_ca_cert = cert.name  # type: ignore

    client = kubernetes.client.ApiClient(configuration=config)
    api = kubernetes.client.CoreV1Api(client)
    #######################################################################
    # Trigger dag
    #######################################################################
    pods = api.list_namespaced_pod(namespace=target_namespace)
    airflow_pod = None
    for pod in pods.items:
        container_status = pod.status.container_statuses[0]
        if pod.metadata.name.find("airflow") != -1 and container_status.ready:
            airflow_pod = pod.metadata.name
            break
    if airflow_pod:
        exec_command = ["/bin/sh", "-c", dag_trigger_command]
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            name=airflow_pod,
            namespace=target_namespace,
            container="scheduler",
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        print("Response: " + resp)
