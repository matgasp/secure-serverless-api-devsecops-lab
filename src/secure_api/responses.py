import json


SECURITY_HEADERS = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
  "Content-Type": "application/json; charset=utf-8",
  "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
  "Referrer-Policy": "no-referrer",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
}


def json_response(status_code, body, request_id):
  payload = dict(body)
  payload["request_id"] = request_id

  return {
    "statusCode": status_code,
    "headers": SECURITY_HEADERS,
    "body": json.dumps(payload, separators=(",", ":"), sort_keys=True),
    "isBase64Encoded": False,
  }
