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
from google.oauth2.service_account import Credentials
from aws_lambda_typing.context import Context as LambdaContext
import boto3
from botocore.exceptions import ClientError
import json


def get_secret_manager() -> boto3.client:
    """
    Retrieves a boto3 secretsmanager client object. If the environmental variable 'integration_test' is set to 'true',
    the client will be connected to a localstack secretsmanager instance at the endpoint 'http://localhost:4566'.
    Otherwise, the client will be connected to the AWS secretsmanager service.
    Returns:
        boto3.client: A boto3 secretsmanager client object.
    """
    secrets_manager_client = boto3.client("secretsmanager")
    integration_test = os.getenv("INTEGRATION_TEST") == "true"
    if integration_test:
        secrets_manager_client.meta.endpoint_url = "http://localhost:4566"
    return secrets_manager_client


def get_credentials(
    secret_manager_client: boto3.client, secret_id: str = "gcp_key"
) -> Credentials:
    """
    Retrieves GCP service account credentials from AWS Secrets Manager.

    Args:
        secret_id (str): The ID of the secret in Secrets Manager. Defaults to "gcp_key".
        secret_manager_client (boto3.client): the secretsmanager client object

    Returns:
        Credentials: The service account credentials object.
    """
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
        credentials: The credentials object to use for generating the token.
        scopes: A list of scopes to include in the token.

    Returns:
        A string representing the access token.
    """
    scopes = [f"https://www.googleapis.com/auth/{s}" for s in scopes]
    scoped = googleapiclient._auth.with_scopes(credentials, scopes)  # type: ignore
    googleapiclient._auth.refresh_credentials(scoped)  # type: ignore
    return scoped.token


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
    api, target_namespace, target_pod_substring, cluster, api_auth_token
):
    api = kubernetes_api(cluster, api_auth_token)
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
    return target_pod_name


def pod_exec(api, target_namespace, target_pod, container, command_string):
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


def lambda_handler(event: dict, context: LambdaContext) -> None:

    #### variables
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    object_uri = f"s3://{bucket_name}/{key}"
    target_namespace = os.getenv("TARGET_NAMESPACE")
    dag = os.getenv("DAG_NAME")
    dag_trigger_command = f"""airflow dags unpause {dag} && airflow dags trigger \
        {dag} --conf '{{"URI":"{object_uri}", "filename":"{key}"}}'"""
    gcp_project = os.getenv("PROJECT")
    gcp_zone = os.getenv("GCP_ZONE")
    gke_name = os.getenv("GKE_CLUSTER_NAME")
    target_pod_substring = os.getenv("TARGET_POD", "airflow")
    target_container = os.getenv("TARGET_CONTAINER", "scheduler")
    #### processing
    secrets_manager_client = get_secret_manager()
    credentials = get_credentials(secrets_manager_client)
    api_auth_token = token(credentials, "cloud-platform")
    gke_cluster = get_cluster_info(gcp_project, gcp_zone, gke_name, credentials)
    api = kubernetes_api(gke_cluster, api_auth_token)
    target_pod_name = get_target_pod(
        api, target_namespace, target_pod_substring, gke_cluster, api_auth_token
    )
    pod_exec(
        api, target_namespace, target_pod_name, target_container, dag_trigger_command
    )
