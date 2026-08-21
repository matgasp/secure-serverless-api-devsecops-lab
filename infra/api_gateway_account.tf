data "aws_iam_policy_document" "api_gateway_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api_gateway_logs" {
  name               = "${local.name}-api-gateway-logs"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role.json
}

resource "aws_iam_role_policy_attachment" "api_gateway_logs" {
  role       = aws_iam_role.api_gateway_logs.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# API Gateway logging configuration is account/region-wide. Use a dedicated lab account.
resource "aws_api_gateway_account" "current" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_logs.arn

  depends_on = [aws_iam_role_policy_attachment.api_gateway_logs]
}
