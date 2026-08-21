resource "aws_api_gateway_rest_api" "api" {
  name        = local.name
  description = "Secure serverless license API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  minimum_compression_size = 1024
}

resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "health"
}

resource "aws_api_gateway_resource" "licenses" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "licenses"
}

resource "aws_api_gateway_resource" "license" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.licenses.id
  path_part   = "{license_id}"
}

resource "aws_api_gateway_resource" "validation" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.license.id
  path_part   = "validate"
}

resource "aws_api_gateway_authorizer" "cognito" {
  name          = "cognito"
  type          = "COGNITO_USER_POOLS"
  rest_api_id   = aws_api_gateway_rest_api.api.id
  provider_arns = [aws_cognito_user_pool.api.arn]
}

resource "aws_api_gateway_method" "route" {
  for_each = local.routes

  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = each.value.resource_id
  http_method   = each.value.http_method
  authorization = each.value.authorization
  authorizer_id = each.value.authorization == "COGNITO_USER_POOLS" ? aws_api_gateway_authorizer.cognito.id : null
}

resource "aws_api_gateway_integration" "route" {
  for_each = local.routes

  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_method.route[each.key].resource_id
  http_method             = aws_api_gateway_method.route[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode({
      methods      = [for value in aws_api_gateway_method.route : value.id]
      integrations = [for value in aws_api_gateway_integration.route : value.id]
      authorizer   = aws_api_gateway_authorizer.cognito.id
    }))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.resourcePath"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      errorType      = "$context.error.responseType"
    })
  }

  xray_tracing_enabled = true

  depends_on = [aws_api_gateway_account.current]
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "ERROR"
    data_trace_enabled     = false
    throttling_rate_limit  = var.throttling_rate_limit
    throttling_burst_limit = var.throttling_burst_limit
  }

  depends_on = [aws_api_gateway_account.current]
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name}"
  retention_in_days = var.log_retention_days
}
