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
from google.oauth2.service_account import Credentials
from aws_lambda_typing.context import Context as LambdaContext
import boto3
from botocore.exceptions import ClientError
import json
from typing import Optional, Any
import re


def extract_target_date(filename: str) -> str:
    """Extracts the date string from a filename and formats it as a date in the 'YYYY-MM-01' format.

    Args:
        filename: The filename to extract the date from.

    Returns:
        string of date in YYYY-MM-01 format.
    """
    match = re.search(r"\d{4}-\d{2}", filename)
    date_string = match.group(0)
    date_parts = date_string.split("-")
    formatted_date = f"{date_parts[0]}-{date_parts[1]}-01"
    return formatted_date


def get_credentials(secret_id: str = "gcp_key") -> Credentials:
    """
    Retrieves GCP service account credentials from AWS Secrets Manager.
    It will initially check if INTEGRATION_TEST env var is set, if true
    it will connect the client to the localstack endpoint, otherwise it
    will be connected to the standard AWS AWS secretsmanager service.

    Args:
        secret_id (str): The ID of the secret in Secrets Manager.
            Defaults to "gcp_key".
        secret_manager_client (boto3.client): the secretsmanager client
            object

    Returns:
        Credentials: The service account credentials object.
    """
    secrets_manager_client = boto3.client("secretsmanager")
    if os.getenv("INTEGRATION_TEST") == "true":
        secrets_manager_client = boto3.client(
            "secretsmanager",
            endpoint_url="http://host.docker.internal:4566",
            region_name="eu-west-1",
        )
    else:
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


def token(credentials: Credentials, *scopes: str) -> str:
    """
    Returns the access token for the given credentials and scopes.

    Args:
        credentials: The credentials object to use for generating
            the token.
        scopes: A list of scopes to include in the token.

    Returns:
        A string representing the access token.
    """
    scopes = [f"https://www.googleapis.com/auth/{s}" for s in scopes]
    scoped = googleapiclient._auth.with_scopes(credentials, scopes)  # type: ignore
    googleapiclient._auth.refresh_credentials(scoped)  # type: ignore
    return scoped.token


def get_cluster_info(
    project: str, zone: str, cluster_name: str, credentials: Credentials
) -> dict[str, Any]:
    """
    Returns the cluster info for the given project, zone, and
    cluster name.

    Args:
        project: The project name.
        zone: The zone where the cluster is located.
        cluster_name: The name of the cluster.
        credentials: The credentials to use for accessing the cluster.

    Returns:
        A dictionary containing the cluster info.

    Raises:
        HttpError: If there is a connection error or the request returns an HTTP error.
    """
    try:
        cluster_attributes = (
            f"projects/{project}/locations/{zone}/clusters/{cluster_name}"
        )
        gke = googleapiclient.discovery.build(
            "container", "v1", credentials=credentials
        )
        gke_clusters = gke.projects().locations().clusters()
        gke_cluster = gke_clusters.get(name=cluster_attributes).execute()
        return gke_cluster
    except HttpError as error:
        print(f"An error occurred while getting cluster info: {error}")
        raise error


def kubernetes_api(
    cluster: dict[str, Any], api_auth_token: str
) -> kubernetes.client.CoreV1Api:
    """
    Returns a Kubernetes API client for the given cluster and API auth token.

    Args:
        cluster: A dictionary containing information about the cluster.
        api_auth_token: The API auth token to use for accessing the cluster.

    Returns:
        A CoreV1Api object for interacting with the Kubernetes API.
    """
    config = kubernetes.client.Configuration()
    config.host = f'https://{cluster["endpoint"]}'
    config.api_key_prefix["authorization"] = "Bearer"
    config.api_key["authorization"] = api_auth_token
    config.debug = False

    with NamedTemporaryFile(delete=False) as cert:
        cert.write(
            base64.decodebytes(cluster["masterAuth"]["clusterCaCertificate"].encode())
        )
        config.ssl_ca_cert = cert.name  # type: ignore

    client = kubernetes.client.ApiClient(configuration=config)
    api = kubernetes.client.CoreV1Api(client)

    return api


def get_target_pod(
    api: kubernetes.client.CoreV1Api,
    target_namespace: str,
    target_pod_substring: str,
    cluster: dict[str, Any],
    api_auth_token: str,
) -> str:
    """
    Returns the name of the first pod in the given namespace that has
    the target pod substring in its name and is ready.

    Args:
        api: A CoreV1Api object for interacting with the Kubernetes API.
        target_namespace: The namespace to search for the target pod.
        target_pod_substring: The substring to search for in the pod names.
        cluster: A dictionary containing information about the cluster.
        api_auth_token: The API auth token to use for accessing the cluster.

    Returns:
        The name of the target pod, or the target pod substring if no matching
        pod is found.
    """
    pods = api.list_namespaced_pod(namespace=str(target_namespace))
    target_pod_name = None
    for pod in pods.items:
        container_status = pod.status.container_statuses[0]
        if (
            pod.metadata.name.find(target_pod_substring) != -1
            and container_status.ready
        ):
            target_pod_name = pod.metadata.name
            break
    if target_pod_name is None:
        return target_pod_substring
    else:
        return target_pod_name


def pod_exec(
    api: kubernetes.client.CoreV1Api,
    target_namespace: str,
    target_pod: str,
    container: str,
    command_string: str,
) -> None:
    """
    Executes the given command string in the specified pod and container
    in the given namespace.

    Args:
        api: A CoreV1Api object for interacting with the Kubernetes API.
        target_namespace: The namespace where the target pod is located.
        target_pod: The name of the target pod.
        container: The name of the container in the target pod.
        command_string: The command to execute in the pod.
    Raises:
        KubernetesError: If there is an error executing the command in the pod.
    """
    try:
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            name=target_pod,
            namespace=target_namespace,
            container=container,
            command=["/bin/sh", "-c", command_string],
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        print("Response: " + resp)
    except kubernetes.client.rest.ApiException as error:
        print(f"An error occurred while executing the command in the pod: {error}")
        raise kubernetes.client.KubernetesError(error)


def lambda_handler(event: dict, context: LambdaContext) -> None:
    """
    Handler for S3 Trigger Lambda.
    Uses the functions above to retrieve credentials, get an
    API auth token, retrieve cluster information, build a
    Kubernetes API client, get the name of the target pod, and
    execute a command in the target pod to trigger a DAG with
    the given URI, filename and run date as configuration.
    """
    #### variables
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    object_uri = f"s3://{bucket_name}/{key}"
    run_date = extract_target_date(key)
    target_namespace = os.getenv("TARGET_NAMESPACE")
    dag = os.getenv("DAG_NAME")
    dag_trigger_command = f"""airflow dags unpause {dag} && airflow  \
        dags trigger {dag} --conf '{{"URI":"{object_uri}", \
        "filename":"{key}", "run_date": "{run_date}"}}'"""
    gcp_project = os.getenv("PROJECT")
    gcp_zone = os.getenv("GCP_ZONE")
    gke_name = os.getenv("GKE_CLUSTER_NAME")
    target_pod_substring = os.getenv("TARGET_POD", "airflow")
    target_container = os.getenv("TARGET_CONTAINER", "scheduler")
    #### processing
    credentials = get_credentials()
    api_auth_token = token(credentials, "cloud-platform")
    gke_cluster = get_cluster_info(gcp_project, gcp_zone, gke_name, credentials)
    api = kubernetes_api(gke_cluster, api_auth_token)
    target_pod_name = get_target_pod(
        api, target_namespace, target_pod_substring, gke_cluster, api_auth_token
    )
    pod_exec(
        api, target_namespace, target_pod_name, target_container, dag_trigger_command
    )
