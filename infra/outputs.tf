output "api_base_url" {
  description = "Base URL for the deployed API."
  value       = aws_api_gateway_stage.api.invoke_url
}

output "aws_region" {
  description = "AWS region containing the deployed lab."
  value       = var.aws_region
}

output "api_stage_arn" {
  description = "API Gateway stage ARN used to verify the regional WAF association."
  value       = aws_api_gateway_stage.api.arn
}

output "cognito_user_pool_id" {
  description = "Cognito user pool identifier."
  value       = aws_cognito_user_pool.api.id
}

output "cognito_client_id" {
  description = "Public Cognito application client identifier."
  value       = aws_cognito_user_pool_client.api.id
}

output "lambda_function_name" {
  description = "Lambda function name."
  value       = aws_lambda_function.api.function_name
}

output "licenses_table_name" {
  description = "DynamoDB table name."
  value       = aws_dynamodb_table.licenses.name
}

output "waf_enabled" {
  description = "Whether the regional WAF protection is enabled."
  value       = var.enable_waf
}

output "waf_web_acl_arn" {
  description = "WAF web ACL ARN when WAF is enabled, otherwise null."
  value       = var.enable_waf ? aws_wafv2_web_acl.api[0].arn : null
}
