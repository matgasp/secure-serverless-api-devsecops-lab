import base64
import binascii
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from secure_api.errors import ApiError


MAX_BODY_BYTES = 16_384
MAX_METADATA_ITEMS = 10
MAX_METADATA_VALUE_LENGTH = 200
PRODUCT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")
SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9:_@.+-]{1,128}$")


def parse_json_body(event):
  headers = {
    str(key).lower(): str(value)
    for key, value in (event.get("headers") or {}).items()
  }
  content_type = headers.get("content-type", "")
  if not content_type.lower().startswith("application/json"):
    raise ApiError(415, "unsupported_media_type", "Content-Type must be application/json")

  body = event.get("body")
  if body is None:
    raise ApiError(400, "invalid_body", "A JSON body is required")

  if event.get("isBase64Encoded"):
    try:
      raw = base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
      raise ApiError(400, "invalid_body", "Body is not valid base64") from None
  else:
    raw = str(body).encode("utf-8")

  if len(raw) > MAX_BODY_BYTES:
    raise ApiError(413, "payload_too_large", "Request body exceeds 16 KiB")

  try:
    payload = json.loads(raw.decode("utf-8"))
  except (UnicodeDecodeError, json.JSONDecodeError):
    raise ApiError(400, "invalid_json", "Body must contain valid UTF-8 JSON") from None

  if not isinstance(payload, dict):
    raise ApiError(400, "invalid_body", "JSON body must be an object")

  return payload


def validate_license_id(raw_value):
  try:
    return str(UUID(str(raw_value)))
  except (ValueError, AttributeError, TypeError):
    raise ApiError(400, "invalid_license_id", "license_id must be a UUID") from None


def validate_create_payload(payload, principal, now):
  allowed = {"product_id", "owner_sub", "expires_at", "metadata"}
  unknown = sorted(set(payload) - allowed)
  if unknown:
    raise ApiError(400, "unknown_fields", f"Unknown fields: {', '.join(unknown)}")

  product_id = payload.get("product_id")
  if not isinstance(product_id, str) or not PRODUCT_PATTERN.fullmatch(product_id):
    raise ApiError(400, "invalid_product_id", "product_id format is invalid")

  owner_sub = payload.get("owner_sub", principal.subject)
  if owner_sub != principal.subject and not principal.is_admin:
    raise ApiError(403, "forbidden", "Only administrators may assign another owner")
  if not isinstance(owner_sub, str) or not SUBJECT_PATTERN.fullmatch(owner_sub):
    raise ApiError(400, "invalid_owner", "owner_sub format is invalid")

  expires_at = _parse_expiration(payload.get("expires_at"), now)
  metadata = _validate_metadata(payload.get("metadata", {}))

  return {
    "product_id": product_id,
    "owner_sub": owner_sub,
    "expires_at": expires_at,
    "metadata": metadata,
  }


def parse_timestamp(raw_value):
  try:
    return datetime.strptime(raw_value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
  except (TypeError, ValueError):
    raise ApiError(400, "invalid_timestamp", "Timestamp must use UTC RFC 3339 format") from None


def _parse_expiration(raw_value, now):
  value = parse_timestamp(raw_value)
  if value <= now:
    raise ApiError(400, "invalid_expiration", "expires_at must be in the future")
  if value > now + timedelta(days=366 * 5):
    raise ApiError(400, "invalid_expiration", "expires_at cannot exceed five years")

  return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_metadata(raw_value):
  if not isinstance(raw_value, dict) or len(raw_value) > MAX_METADATA_ITEMS:
    raise ApiError(400, "invalid_metadata", "metadata must contain at most 10 items")

  result = {}
  for key, value in raw_value.items():
    if not isinstance(key, str) or not PRODUCT_PATTERN.fullmatch(key):
      raise ApiError(400, "invalid_metadata", "metadata keys have an invalid format")
    if not isinstance(value, str) or len(value) > MAX_METADATA_VALUE_LENGTH:
      raise ApiError(400, "invalid_metadata", "metadata values must be short strings")

    result[key] = value

  return result
