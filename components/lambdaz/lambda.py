import io
import os
import urllib.parse

import boto3
from google.oauth2 import service_account

from lambda_utils import *

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    os.environ["LAMBDA_TASK_ROOT"] + "/lambda_key.json"
)
s3 = boto3.client("s3")


credentials = service_account.Credentials.from_service_account_file("lambda_key.json")


def lambda_handler(event: dict, context) -> None:
    """
    A lambda function that is triggered by the addition/creation of a file in a target bucket. When triggered will load the newly added files to a backup GCS bucket.
    It will check if file exists first, if it doesn't, it will upload the binary file to GCS.

    :param dict event: data passed through the triggering event.
    :param LambdaContext context: provides information about the current execution environment
    :raises e: if the function fails, an error is raised.
    :return dict: _description_
    """
    GCS_BUCKET = os.getenv("STAGING_BUCKET")
    GCP_PROJECT = os.getenv("GCP_PROJECT")
    GCP_ZONE = os.getenv("GCP_ZONE")
    CLUSTER_NAME = os.getenv("CLUSTER_NAME")
    NODE_POOL_NAME = os.getenv("NODE_POOL_NAME")
    JOBS_NODE_POOL_SIZE = int(os.getenv("JOBS_NODE_POOL_SIZE", 4))
    try:
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        # Download file from S3 bucket
        data_stream = io.BytesIO()
        s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=data_stream)

        # Upload to cloud storage
        gcs_path = file_name_constructor(key)
        if not check_existence(GCS_BUCKET, gcs_path):  # type: ignore
            print("upscaling_gke")
            request = upscale_gke(
                GCP_PROJECT,
                GCP_ZONE,
                CLUSTER_NAME,
                NODE_POOL_NAME,
                JOBS_NODE_POOL_SIZE,
            )
            wait_for_operation(request, GCP_PROJECT, GCP_ZONE)
            upload_to_gcs(gcs_path, data_stream, GCS_BUCKET)  # type: ignore
        else:
            print(f"file already exists at {gcs_path}, terminating run.")

    except Exception as e:
        print(e)
        print("Error in object transfer.")
        raise e
