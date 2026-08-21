locals {
  name = "${var.project_name}-${var.environment}"

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
    SecurityLab = "true"
  }

  routes = {
    health_get = {
      resource_id   = aws_api_gateway_resource.health.id
      http_method   = "GET"
      authorization = "NONE"
    }
    licenses_post = {
      resource_id   = aws_api_gateway_resource.licenses.id
      http_method   = "POST"
      authorization = "COGNITO_USER_POOLS"
    }
    license_get = {
      resource_id   = aws_api_gateway_resource.license.id
      http_method   = "GET"
      authorization = "COGNITO_USER_POOLS"
    }
    license_delete = {
      resource_id   = aws_api_gateway_resource.license.id
      http_method   = "DELETE"
      authorization = "COGNITO_USER_POOLS"
    }
    validation_post = {
      resource_id   = aws_api_gateway_resource.validation.id
      http_method   = "POST"
      authorization = "COGNITO_USER_POOLS"
    }
  }
}
