import os
from tempfile import NamedTemporaryFile
import kubernetes.client
import base64
import googleapiclient.discovery
import kubernetes
from kubernetes.stream import stream
import googleapiclient.discovery
import os
import urllib.parse
import logging

from google.oauth2 import service_account

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    os.environ["LAMBDA_TASK_ROOT"] + "/lambda_key.json"
)


def lambda_handler(event: dict, context) -> None:

    #######################################################################
    # setup variables
    #######################################################################
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )
    object_uri = f"s3://{bucket_name}/{key}"
    cluster_data = f'projects/{os.getenv("PROJECT")}/locations/{os.getenv("GCP_ZONE")}/clusters/{os.getenv("GKE_CLUSTER_NAME")}'
    logger.info(f"cluster_data = {cluster_data}")
    DAG_NAME = os.getenv("DAG_NAME")
    NAMESPACE = os.getenv("TARGET_NAMESPACE")
    COMMAND_STRING = f"""airflow dags unpause {DAG_NAME} && airflow dags trigger {DAG_NAME} --conf '{{"URI":"{object_uri}"}}'"""
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
        exec_cmd = stream(
            api.connect_post_namespaced_pod_exec(
                airflow_pod,
                namespace=NAMESPACE,
                command=COMMAND_STRING,
                container="scheduler",
            )
        )

        print(exec_cmd)
