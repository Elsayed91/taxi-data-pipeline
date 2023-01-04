resource "aws_iam_role" "lambda_role" {
  name = "iam_for_lambda_tf"

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

resource "aws_iam_role_policy" "revoke_keys_role_policy" {
  name = "lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:*",
        "ses:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_lambda_permission" "allow_bucket" {
  for_each      = { for idx, val in var.lambda : idx => val if val.trigger_bucket != null }
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_func[each.key].arn
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${each.value.trigger_bucket}"
}

resource "null_resource" "pack-lambda" {
  for_each = { for idx, val in var.lambda : idx => val if var.lambda != null }
  triggers = {
    hashed_content = jsonencode({ for fn in fileset("${path.module}/${each.value.code_path}", "**") :
    fn => filesha256("${path.module}/${each.value.code_path}/${fn}") })
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = "chmod +x ${path.module}/files/package_fn_code.sh && ${path.module}/files/package_fn_code.sh lambda"
  }
  depends_on = [
    local_file.key_out
  ]
}




data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/files/lambda/"
  output_path = "${path.module}/files/dependencies.zip"
  depends_on = [
    null_resource.pack-lambda
  ]
}


resource "aws_lambda_function" "lambda_func" {
  for_each         = { for idx, val in var.lambda : idx => val if val.trigger_bucket != null }
  function_name    = each.value.name
  filename         = "${path.module}/files/dependencies.zip"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256 #filebase64sha256("${path.module}/my-deployment-package.zip")
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.9"
  handler          = "main.lambda_handler"
  # layers           = [aws_lambda_layer_version.pubsub-layer.arn]
  timeout     = 30
  memory_size = 512
  environment {
    variables = each.value.vars
  }
  depends_on = [
    data.archive_file.lambda_zip
  ]
}

resource "aws_s3_bucket_notification" "aws-lambda-s3-trigger" {
  for_each = { for idx, val in var.lambda : idx => val if val.trigger_bucket != null }
  bucket   = each.value.trigger_bucket
  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_func[each.key].arn
    events              = ["s3:ObjectCreated:*"]
    #    filter_prefix       = "AWSLogs/"
    filter_suffix = ".parquet"

  }
  depends_on = [
    aws_s3_bucket.bucket
  ]
}


resource "aws_cloudwatch_log_group" "function_log_group" {
  for_each          = { for idx, val in var.lambda : idx => val if val.trigger_bucket != null }
  name              = "/aws/lambda/${aws_lambda_function.lambda_func[each.key].function_name}"
  retention_in_days = 1
  lifecycle {
    prevent_destroy = false
  }

}

resource "aws_iam_policy" "function_logging_policy" {
  name = "function-logging-policy2"
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
