resource "aws_wafv2_web_acl" "api" {
  count = var.enable_waf ? 1 : 0

  name  = "${local.name}-rate-limit"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "ip-rate-limit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        aggregate_key_type = "IP"
        limit              = var.waf_rate_limit
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name}-ip-rate-limit"
      sampled_requests_enabled   = false
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name}-waf"
    sampled_requests_enabled   = false
  }
}

resource "aws_wafv2_web_acl_association" "api" {
  count = var.enable_waf ? 1 : 0

  resource_arn = aws_api_gateway_stage.api.arn
  web_acl_arn  = aws_wafv2_web_acl.api[0].arn
}
