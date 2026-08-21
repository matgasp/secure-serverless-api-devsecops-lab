resource "aws_cognito_user_pool" "api" {
  name                     = "${local.name}-users"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  deletion_protection = "INACTIVE"

  password_policy {
    minimum_length                   = 14
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 2
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

}

resource "aws_cognito_user_pool_client" "api" {
  name         = "${local.name}-client"
  user_pool_id = aws_cognito_user_pool.api.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  access_token_validity                = 15
  id_token_validity                    = 15
  refresh_token_validity               = 7
  explicit_auth_flows                  = ["ALLOW_USER_SRP_AUTH", "ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_flows_user_pool_client = false

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.api.id
  description  = "Administrators permitted to manage licenses across owners."
  precedence   = 10
}
