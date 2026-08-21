resource "aws_dynamodb_table" "licenses" {
  name         = "${local.name}-licenses"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "license_id"

  attribute {
    name = "license_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }
}
