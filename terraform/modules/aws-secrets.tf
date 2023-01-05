# this module creates AWS secrets in the AWS[Secrets] section of the config file
# Note that normally you want the secrets rotated at fixed intervals, this is 
# usually done witha lambda function, however due to billing concerns of create
# and forget on AWS, I have set it to auto delete in 30 days for the project's 
# purposes.

resource "aws_secretsmanager_secret" "secret" {
  for_each                = { for idx, secret in var.s3-secrets : idx => secret if var.s3-secrets != null }
  name                    = each.value.name
  recovery_window_in_days = 30

  # rotation_lambda_arn     = aws_lambda_function.rotation_lambda.arn
}

resource "aws_secretsmanager_secret_version" "secret_content" {
  for_each      = { for idx, secret in var.s3-secrets : idx => secret if var.s3-secrets != null }
  secret_id     = aws_secretsmanager_secret.secret[each.key].id
  secret_string = each.value.type == "string" ? each.value.secret_string : file("${path.module}/${each.value.secret_string}")
}

# resource "aws_lambda_function" "rotation_lambda" {
#   filename      = "rotation_lambda.zip"
#   function_name = "rotation_lambda"
#   role          = aws_iam_role.iam_for_lambda.arn
#   handler       = "exports.handler"
#   runtime       = "nodejs12.x"

#   environment {
#     variables = {
#       EXAMPLE_VAR = "example value"
#     }
#   }
# }

# resource "aws_iam_role" "iam_for_lambda" {
#   name = "iam_for_lambda"

#   assume_role_policy = <<EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Action": "sts:AssumeRole",
#       "Principal": {
#         "Service": "lambda.amazonaws.com"
#       },
#       "Effect": "Allow",
#       "Sid": ""
#     }
#   ]
# }
# EOF
# }
