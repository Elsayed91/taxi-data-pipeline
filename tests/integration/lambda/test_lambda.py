import os
import unittest

import boto3


def test_lambda_response(self):
    client = boto3.client(service_name="lambda", endpoint_url="http://localhost:4566")
    response = client.invoke(
        FunctionName="test-lambda", InvocationType="RequestResponse"
    )
    assert response["StatusCode"] == 200
    assert response["Payload"]
    html = response["Payload"].read().decode("utf-8")
    # Check if "Example Domain" text exists in example.com
    assert "Example Domain" in html
