variable "aws_region" {
  description = "AWS region used by all resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Short environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.environment))
    error_message = "environment must be a short lowercase identifier."
  }
}

variable "project_name" {
  description = "Resource name prefix."
  type        = string
  default     = "secure-serverless-api"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "project_name must be a lowercase kebab-case identifier."
  }
}

variable "lambda_package_path" {
  description = "Path to the Lambda deployment ZIP."
  type        = string
  default     = "../dist/lambda.zip"
}

variable "log_retention_days" {
  description = "CloudWatch log retention."
  type        = number
  default     = 30
}

variable "lambda_reserved_concurrency" {
  description = "Concurrency ceiling to contain cost and blast radius."
  type        = number
  default     = 10
}

variable "throttling_rate_limit" {
  description = "Steady API requests per second."
  type        = number
  default     = 20
}

variable "throttling_burst_limit" {
  description = "Maximum API request burst."
  type        = number
  default     = 40
}

variable "enable_waf" {
  description = "Attach a regional WAF rate-based rule. WAF creates additional AWS charges."
  type        = bool
  default     = false
}

variable "waf_rate_limit" {
  description = "Requests allowed per five-minute WAF evaluation window for one IP."
  type        = number
  default     = 500

  validation {
    condition     = var.waf_rate_limit >= 10
    error_message = "waf_rate_limit must be at least 10."
  }
}

variable "enable_point_in_time_recovery" {
  description = "Enable DynamoDB point-in-time recovery."
  type        = bool
  default     = true
}

variable "enable_alarms" {
  description = "Create CloudWatch alarms for Lambda errors and API 5xx responses."
  type        = bool
  default     = true
}
