# terraform/localstack.tf
provider "aws" {
  region                      = "eu-west-1"
  access_key                  = "fakekey"
  secret_key                  = "fakekey"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    lambda         = "http://localhost:4566"
    iam            = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    s3             = "http://localhost:4566"
    logs           = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "bucket" {
  bucket = "test-bucket"

}

resource "aws_s3_bucket_acl" "bucketacl" {
  bucket = aws_s3_bucket.bucket.id
  acl    = "public-read"
}



resource "aws_iam_role" "lambda_role" {
  name = "test_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "aws_iam_policy" "AmazonS3FullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "AmazonS3FullAccess-policy" {
  role       = aws_iam_role.lambda_role.id
  policy_arn = data.aws_iam_policy.AmazonS3FullAccess.arn
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bucket.arn
}


data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/files"
  output_path = "${path.module}/dependencies.zip"

}


resource "aws_lambda_function" "lambda_func" {
  function_name    = "test-lambda"
  filename         = "${path.module}/dependencies.zip"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256 #filebase64sha256("${path.module}/my-deployment-package.zip")
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.9"
  handler          = "main.lambda_handler"
  # layers           = [aws_lambda_layer_version.pubsub-layer.arn]
  timeout     = 30
  memory_size = 128
  environment {
    variables = {
      PROJECT          = "stellarismus"
      GCP_ZONE         = "europe-west1-d"
      GKE_CLUSTER_NAME = "gke"
      DAG_NAME         = "lambda_integration_test"
      TARGET_NAMESPACE = "default"
      INTEGRATION_TEST = true
    }
  }
  depends_on = [
    data.archive_file.lambda_zip
  ]
}

resource "aws_s3_bucket_notification" "aws-lambda-s3-trigger" {
  bucket = "test-bucket"
  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_func.arn
    events              = ["s3:ObjectCreated:*"]
    #    filter_prefix       = "AWSLogs/"
    # filter_suffix = ".parquet"

  }
  depends_on = [
    aws_s3_bucket.bucket
  ]
}



resource "aws_cloudwatch_log_group" "function_log_group" {
  name              = "/aws/lambda/test_lambda"
  retention_in_days = 1
  lifecycle {
    prevent_destroy = false
  }

}

resource "aws_iam_policy" "function_logging_policy" {
  name = "function-logging-policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
        ],
        Effect : "Allow",
        Resource : "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "function_logging_policy_attachment" {
  role       = aws_iam_role.lambda_role.id
  policy_arn = aws_iam_policy.function_logging_policy.arn
}
