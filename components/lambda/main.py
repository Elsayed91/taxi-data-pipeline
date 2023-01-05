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
from base64 import decodebytes, encode

import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_credentials(secret_id: str = "gcp_key"):
    secrets_manager_client = boto3.client("secretsmanager")
    get_secret_value_response = secrets_manager_client.get_secret_value(
        SecretId=secret_id
    )
    key_file = get_secret_value_response["SecretString"]
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(key_file, f)
        f.flush()

    # Load the credentials from the temporary file
    credentials = Credentials.from_service_account_file(f.name)

    # Delete the temporary file
    os.unlink(f.name)

    return credentials


def lambda_handler(event: dict, context: LambdaContext) -> None:

    #######################################################################
    # setup variables
    #######################################################################
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    object_uri = f"s3://{bucket_name}/{key}"
    cluster_name = f'projects/{os.getenv("PROJECT")}/locations/{os.getenv("GCP_ZONE")}/clusters/{os.getenv("GKE_CLUSTER_NAME")}'
    namespace = os.getenv("TARGET_NAMESPACE")
    command = f"""airflow dags unpause {os.getenv("DAG_NAME")} && airflow dags trigger {os.getenv("DAG_NAME")} --conf '{{"URI":"{object_uri}", "filename":"{key}"}}'"""
    #######################################################################
    # setup gke connection
    #######################################################################

    print(get_credentials())

    secrets_manager_client = boto3.client("secretsmanager")
    get_secret_value_response = secrets_manager_client.get_secret_value(
        SecretId="gcp-key"
    )
    key_file = get_secret_value_response["SecretString"]
    service_account_info = json.loads(key_file)
    credentials = Credentials.from_service_account_info(service_account_info)
    print(credentials)
    # credentials = service_account.Credentials.from_service_account_file(
    #     "lambda_key.json"
    # )
    # scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    # scoped = googleapiclient._auth.with_scopes(credentials, scopes)  # type: ignore
    # googleapiclient._auth.refresh_credentials(scoped)  # type: ignore
    # api_auth_token = scoped.token
    # gke = googleapiclient.discovery.build("container", "v1", credentials=credentials)
    # gke_clusters = gke.projects().locations().clusters()
    # gke_cluster = gke_clusters.get(name=CLUSTER_NAME).execute()
    # config = kubernetes.client.Configuration()
    # config.host = f'https://{gke_cluster["endpoint"]}'
    # config.api_key_prefix["authorization"] = "Bearer"
    # config.api_key["authorization"] = api_auth_token
    # config.debug = False
    # with NamedTemporaryFile(delete=False) as cert:
    #     cert.write(
    #         decodebytes(
    #             gke_cluster["masterAuth"]["clusterCaCertificate"].encode()
    #         )
    #     )
    #     config.ssl_ca_cert = cert.name  # type: ignore

    # client = kubernetes.client.ApiClient(configuration=config)
    # api = kubernetes.client.CoreV1Api(client)
    # #######################################################################
    # # Trigger dag
    # #######################################################################
    # pods = api.list_namespaced_pod(namespace=NAMESPACE)
    # airflow_pod = None
    # for pod in pods.items:
    #     if pod.metadata.name.find("airflow") != -1:
    #         airflow_pod = pod.metadata.name
    #         break
    # if airflow_pod:
    #     exec_command = ["/bin/sh", "-c", COMMAND_STRING]
    #     resp = stream(
    #         api.connect_get_namespaced_pod_exec,
    #         name=airflow_pod,
    #         namespace=NAMESPACE,
    #         container="scheduler",
    #         command=exec_command,
    #         stderr=True,
    #         stdin=False,
    #         stdout=True,
    #         tty=False,
    #     )
    #     print("Response: " + resp)
