import time
from typing import TextIO

from google.cloud import storage
from google.cloud.container_v1 import ClusterManagerClient, SetNodePoolSizeRequest
from google.cloud.container_v1.types import Operation


def upscale_gke(project, zone, cluster_name, node_pool_name, node_count):
    client = ClusterManagerClient()
    request = SetNodePoolSizeRequest(
        name=f"projects/{project}/locations/{zone}/clusters/{cluster_name}/nodePools/{node_pool_name}",
        node_count=node_count,
    )
    response = client.set_node_pool_size(request=request)
    print(response)
    return response


def get_operation(operation, project, zone):
    client = ClusterManagerClient()
    req = f"projects/{project}/locations/{zone}/operations/{operation}"
    return client.get_operation(name=req)


def wait_for_operation(operation, project, zone):
    while operation.status != Operation.Status.DONE:
        if (
            operation.status == Operation.Status.RUNNING
            or operation.status == Operation.Status.PENDING
        ):
            time.sleep(15)
        else:
            print(f"Operation has failed with status: {operation.status}")

        # To update status of operation
        operation = get_operation(operation.name, project, zone)
    print("upscaled.")
    return operation


def file_name_constructor(file_name: str) -> str:
    """generates the expected path of the blob based on pre-defined conventions.

    :param str file_name: name of the file that will be uploaded to GCS.
    :return str: returns the full path
    EX: yellow_tripdata_2010.parquet would return -> yellow_trip_data/yellow_tripdata_2010.parquet where yellow_trip_data is the folder where the file should be uploaded to.
    In case the file does not meet the naing convention, it will be returned as is, and will be placed in the root directory of the bucket.
    """
    try:
        file_expected_folder = f'{file_name.split("_")[0]}'
        name = f"{file_expected_folder}/{file_name}"
        return name
    except Exception as e:
        name = file_name
        return name
        print(e)


def check_existence(bucket: str, full_path: str) -> bool:
    """A check to ensure idempotency. before attempting to upload a file, a check will be run to look for the file in the expected destination.
    If found, the Lambda function will not take any further actions.

    :param str bucket: bucket where the file is expected to be in.
    :param str full_path: the path of the file within the bucket.
    :return bool: true if the file exists, false if it doesn't.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)  # type: ignore
    exists_in_bucket = storage.Blob(bucket=bucket, name=full_path).exists()
    return exists_in_bucket


def upload_to_gcs(blob_name: str, binary_file: TextIO, bucket: str) -> None:
    """Uploads a binary file to GCS.

    :param str blob_name: the name that the file will have in GCS.
    :param FileIO[bytes] binary_file: the path to the binary file.
    :param str bucket: the bucket wherein the file will be uploaded.
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket)  # type: ignore
    blob = bucket.blob(blob_name)  # type: ignore
    blob.upload_from_file(binary_file, rewind=True)
