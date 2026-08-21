resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "api" {
  function_name = local.name
  description   = "Secure license API for the DevSecOps lab"
  role          = aws_iam_role.lambda.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.14"
  architectures = ["x86_64"]

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  memory_size                    = 256
  timeout                        = 10
  reserved_concurrent_executions = var.lambda_reserved_concurrency

  environment {
    variables = {
      LICENSES_TABLE = aws_dynamodb_table.licenses.name
      LOG_LEVEL      = "INFO"
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda,
  ]
}
