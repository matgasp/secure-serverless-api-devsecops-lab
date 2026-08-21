import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from secure_api.handler import Api  # noqa: E402


NOW = datetime(2027, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
LICENSE_ID = "11111111-1111-4111-8111-111111111111"


class FakeRepository:
  def __init__(self):
    self.items = {}

  def put(self, item):
    self.items[item["license_id"]] = dict(item)

  def get(self, license_id):
    item = self.items.get(license_id)
    return dict(item) if item else None

  def mark_validated(self, license_id, validated_at):
    self.items[license_id]["last_validated_at"] = validated_at

  def delete(self, license_id):
    del self.items[license_id]


class Context:
  aws_request_id = "test-request"


def event(method, resource, subject="user-a", groups="", body=None, license_id=None):
  value = {
    "httpMethod": method,
    "resource": resource,
    "headers": {"Content-Type": "application/json"},
    "requestContext": {
      "requestId": "gateway-request",
      "authorizer": {
        "claims": {
          "sub": subject,
          "cognito:username": subject,
          "cognito:groups": groups,
        }
      },
    },
    "pathParameters": {},
    "isBase64Encoded": False,
  }
  if body is not None:
    value["body"] = json.dumps(body) if not isinstance(body, str) else body
  if license_id is not None:
    value["pathParameters"]["license_id"] = license_id

  return value


def response_body(response):
  return json.loads(response["body"])


class ApiTests(unittest.TestCase):
  def setUp(self):
    self.repository = FakeRepository()
    self.api = Api(self.repository, now=lambda: NOW)

  def seed(self, owner="user-a", expires_at="2027-02-01T12:00:00Z", revoked=False):
    self.repository.items[LICENSE_ID] = {
      "license_id": LICENSE_ID,
      "product_id": "secure-api",
      "owner_sub": owner,
      "expires_at": expires_at,
      "metadata": {},
      "created_at": "2026-12-01T12:00:00Z",
      "created_by": "admin-a",
      "revoked": revoked,
    }

  def test_health_is_public_and_has_security_headers(self):
    response = self.api.handle({"httpMethod": "GET", "resource": "/health"}, Context())

    self.assertEqual(200, response["statusCode"])
    self.assertEqual("no-store", response["headers"]["Cache-Control"])
    self.assertEqual("nosniff", response["headers"]["X-Content-Type-Options"])

  def test_missing_authentication_is_rejected(self):
    request = event("POST", "/licenses", body={})
    request["requestContext"]["authorizer"] = {}

    response = self.api.handle(request, Context())

    self.assertEqual(401, response["statusCode"])
    self.assertEqual("unauthorized", response_body(response)["error"]["code"])

  def test_user_can_create_license_for_self(self):
    request = event(
      "POST",
      "/licenses",
      body={
        "product_id": "desktop-agent",
        "expires_at": "2027-03-01T12:00:00Z",
        "metadata": {"tier": "standard"},
      },
    )

    response = self.api.handle(request, Context())
    created = response_body(response)["license"]

    self.assertEqual(201, response["statusCode"])
    self.assertEqual("user-a", created["owner_sub"])
    self.assertNotIn("created_by", created)

  def test_non_admin_cannot_override_owner(self):
    request = event(
      "POST",
      "/licenses",
      body={
        "product_id": "desktop-agent",
        "owner_sub": "user-b",
        "expires_at": "2027-03-01T12:00:00Z",
      },
    )

    response = self.api.handle(request, Context())

    self.assertEqual(403, response["statusCode"])

  def test_admin_can_assign_another_owner(self):
    request = event(
      "POST",
      "/licenses",
      groups="admin",
      body={
        "product_id": "desktop-agent",
        "owner_sub": "user-b",
        "expires_at": "2027-03-01T12:00:00Z",
      },
    )

    response = self.api.handle(request, Context())

    self.assertEqual(201, response["statusCode"])
    self.assertEqual("user-b", response_body(response)["license"]["owner_sub"])

  def test_cross_owner_access_returns_not_found(self):
    self.seed(owner="user-b")

    response = self.api.handle(
      event("GET", "/licenses/{license_id}", license_id=LICENSE_ID),
      Context(),
    )

    self.assertEqual(404, response["statusCode"])

  def test_active_license_is_valid(self):
    self.seed()

    response = self.api.handle(
      event("POST", "/licenses/{license_id}/validate", license_id=LICENSE_ID),
      Context(),
    )

    body = response_body(response)
    self.assertEqual(200, response["statusCode"])
    self.assertTrue(body["valid"])
    self.assertEqual("active", body["reason"])

  def test_expired_license_is_invalid(self):
    self.seed(expires_at="2026-12-01T12:00:00Z")

    response = self.api.handle(
      event("POST", "/licenses/{license_id}/validate", license_id=LICENSE_ID),
      Context(),
    )

    body = response_body(response)
    self.assertFalse(body["valid"])
    self.assertEqual("expired", body["reason"])

  def test_revoked_license_is_invalid(self):
    self.seed(revoked=True)

    response = self.api.handle(
      event("POST", "/licenses/{license_id}/validate", license_id=LICENSE_ID),
      Context(),
    )

    body = response_body(response)
    self.assertFalse(body["valid"])
    self.assertEqual("revoked", body["reason"])

  def test_admin_can_read_another_owners_license(self):
    self.seed(owner="user-b")

    response = self.api.handle(
      event("GET", "/licenses/{license_id}", groups="admin", license_id=LICENSE_ID),
      Context(),
    )

    self.assertEqual(200, response["statusCode"])

  def test_only_admin_can_delete(self):
    self.seed()

    denied = self.api.handle(
      event("DELETE", "/licenses/{license_id}", license_id=LICENSE_ID),
      Context(),
    )
    allowed = self.api.handle(
      event(
        "DELETE",
        "/licenses/{license_id}",
        groups="admin",
        license_id=LICENSE_ID,
      ),
      Context(),
    )

    self.assertEqual(403, denied["statusCode"])
    self.assertEqual(200, allowed["statusCode"])
    self.assertNotIn(LICENSE_ID, self.repository.items)

  def test_malformed_json_is_rejected(self):
    request = event("POST", "/licenses", body="{")

    response = self.api.handle(request, Context())

    self.assertEqual(400, response["statusCode"])
    self.assertEqual("invalid_json", response_body(response)["error"]["code"])

  def test_oversized_body_is_rejected(self):
    request = event("POST", "/licenses", body="x" * 16_385)

    response = self.api.handle(request, Context())

    self.assertEqual(413, response["statusCode"])

  def test_unknown_fields_are_rejected(self):
    request = event(
      "POST",
      "/licenses",
      body={
        "product_id": "desktop-agent",
        "expires_at": "2027-03-01T12:00:00Z",
        "role": "admin",
      },
    )

    response = self.api.handle(request, Context())

    self.assertEqual(400, response["statusCode"])
    self.assertEqual("unknown_fields", response_body(response)["error"]["code"])

  def test_non_json_content_type_is_rejected(self):
    request = event(
      "POST",
      "/licenses",
      body={"product_id": "desktop-agent", "expires_at": "2027-03-01T12:00:00Z"},
    )
    request["headers"]["Content-Type"] = "text/plain"

    response = self.api.handle(request, Context())

    self.assertEqual(415, response["statusCode"])

  def test_invalid_license_identifier_is_rejected(self):
    self.seed()

    response = self.api.handle(
      event("GET", "/licenses/{license_id}", license_id="../admin"),
      Context(),
    )

    self.assertEqual(400, response["statusCode"])


if __name__ == "__main__":
  unittest.main()
