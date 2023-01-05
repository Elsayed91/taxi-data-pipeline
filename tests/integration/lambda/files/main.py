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
-   Using environment variables for sensitive information such as API keys, project names, and bucket names.
-   Using a temporary file to store the GKE cluster certificate instead of storing it in a variable, 
    preventing it from being exposed in memory.
-   Using the NamedTemporaryFile context manager to create a temporary file, which automatically deletes the
    file after it is closed.
    
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
from google.oauth2 import service_account
from aws_lambda_typing.context import Context as LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> None:

    #######################################################################
    # setup variables
    #######################################################################
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    object_uri = f"s3://{bucket_name}/{key}"
    cluster_data = f'projects/{os.getenv("PROJECT")}/locations/{os.getenv("GCP_ZONE")}/clusters/{os.getenv("GKE_CLUSTER_NAME")}'
    DAG_NAME = os.getenv("DAG_NAME")
    NAMESPACE = os.getenv("TARGET_NAMESPACE")
    COMMAND_STRING = f"""airflow dags unpause {DAG_NAME} && airflow dags trigger {DAG_NAME} --conf '{{"URI":"{object_uri}", "filename":"{key}"}}'"""
    #######################################################################
    # setup gke connection
    #######################################################################
    credentials = service_account.Credentials.from_service_account_file(
        "lambda_key.json"
    )
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    scoped = googleapiclient._auth.with_scopes(credentials, scopes)  # type: ignore
    googleapiclient._auth.refresh_credentials(scoped)  # type: ignore
    api_auth_token = scoped.token
    gke = googleapiclient.discovery.build("container", "v1", credentials=credentials)
    gke_clusters = gke.projects().locations().clusters()
    gke_cluster = gke_clusters.get(name=cluster_data).execute()
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
    pods = api.list_namespaced_pod(namespace=NAMESPACE)
    airflow_pod = None
    for pod in pods.items:
        if pod.metadata.name.find("airflow") != -1:
            airflow_pod = pod.metadata.name
            break
    if airflow_pod:
        exec_command = ["/bin/sh", "-c", COMMAND_STRING]
        resp = stream(
            api.connect_get_namespaced_pod_exec,
            name=airflow_pod,
            namespace=NAMESPACE,
            container="scheduler",
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        print("Response: " + resp)