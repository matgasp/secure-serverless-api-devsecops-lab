from datetime import datetime, timezone
from uuid import uuid4

from secure_api.auth import principal_from_event
from secure_api.errors import ApiError
from secure_api.logging_utils import log_event
from secure_api.responses import json_response
from secure_api.validation import (
  parse_json_body,
  parse_timestamp,
  validate_create_payload,
  validate_license_id,
)


class Api:
  def __init__(self, repository, now=None):
    self._repository = repository
    self._now = now or (lambda: datetime.now(timezone.utc))

  def handle(self, event, context):
    request_id = _request_id(event, context)
    method = str(event.get("httpMethod", "")).upper()
    resource = event.get("resource") or event.get("path") or ""

    try:
      if method == "GET" and resource == "/health":
        return json_response(200, {"status": "ok"}, request_id)

      principal = principal_from_event(event)
      path_parameters = event.get("pathParameters") or {}

      if method == "POST" and resource == "/licenses":
        return self._create(event, principal, request_id)
      if method == "GET" and resource == "/licenses/{license_id}":
        return self._get(path_parameters, principal, request_id)
      if method == "POST" and resource == "/licenses/{license_id}/validate":
        return self._validate(path_parameters, principal, request_id)
      if method == "DELETE" and resource == "/licenses/{license_id}":
        return self._delete(path_parameters, principal, request_id)

      raise ApiError(404, "not_found", "Resource not found")
    except ApiError as error:
      log_event(
        "warning",
        "request_rejected",
        request_id=request_id,
        method=method,
        resource=resource,
        status_code=error.status_code,
        error_code=error.code,
      )

      return json_response(
        error.status_code,
        {"error": {"code": error.code, "message": error.message}},
        request_id,
      )
    except Exception:
      log_event(
        "exception",
        "unhandled_error",
        request_id=request_id,
        method=method,
        resource=resource,
      )

      return json_response(
        500,
        {
          "error": {
            "code": "internal_error",
            "message": "Request could not be completed",
          },
        },
        request_id,
      )

  def _create(self, event, principal, request_id):
    now = self._now()
    values = validate_create_payload(parse_json_body(event), principal, now)
    item = {
      "license_id": str(uuid4()),
      **values,
      "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
      "created_by": principal.subject,
      "revoked": False,
    }

    self._repository.put(item)
    log_event(
      "info",
      "license_created",
      request_id=request_id,
      license_id=item["license_id"],
    )

    return json_response(201, {"license": _public_item(item)}, request_id)

  def _get(self, path_parameters, principal, request_id):
    item = self._authorized_item(path_parameters, principal)

    return json_response(200, {"license": _public_item(item)}, request_id)

  def _validate(self, path_parameters, principal, request_id):
    item = self._authorized_item(path_parameters, principal)
    now = self._now()
    is_expired = parse_timestamp(item["expires_at"]) <= now
    is_valid = not item.get("revoked", False) and not is_expired
    reason = "active" if is_valid else ("revoked" if item.get("revoked") else "expired")
    validated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    self._repository.mark_validated(item["license_id"], validated_at)

    return json_response(
      200,
      {
        "license_id": item["license_id"],
        "valid": is_valid,
        "reason": reason,
        "validated_at": validated_at,
      },
      request_id,
    )

  def _delete(self, path_parameters, principal, request_id):
    if not principal.is_admin:
      raise ApiError(403, "forbidden", "Administrator access is required")

    license_id = validate_license_id(path_parameters.get("license_id"))
    if not self._repository.get(license_id):
      raise ApiError(404, "not_found", "License not found")

    self._repository.delete(license_id)
    log_event("info", "license_deleted", request_id=request_id, license_id=license_id)

    return json_response(200, {"deleted": True, "license_id": license_id}, request_id)

  def _authorized_item(self, path_parameters, principal):
    license_id = validate_license_id(path_parameters.get("license_id"))
    item = self._repository.get(license_id)

    # Return 404 for cross-owner access to reduce resource enumeration.
    if not item or (item.get("owner_sub") != principal.subject and not principal.is_admin):
      raise ApiError(404, "not_found", "License not found")

    return item


def _request_id(event, context):
  if context and getattr(context, "aws_request_id", None):
    return context.aws_request_id

  return event.get("requestContext", {}).get("requestId", "unknown")


def _public_item(item):
  allowed = {
    "license_id",
    "product_id",
    "owner_sub",
    "expires_at",
    "metadata",
    "created_at",
    "revoked",
    "last_validated_at",
  }

  return {key: value for key, value in item.items() if key in allowed}
