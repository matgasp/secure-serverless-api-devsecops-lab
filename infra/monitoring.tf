resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name}-lambda-errors"
  alarm_description   = "Lambda returned at least one error in five minutes."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${local.name}-api-5xx"
  alarm_description   = "API Gateway returned at least one 5xx response in five minutes."
  namespace           = "AWS/ApiGateway"
  metric_name         = "5XXError"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.api.name
    Stage   = aws_api_gateway_stage.api.stage_name
  }
}
