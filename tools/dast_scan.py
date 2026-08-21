import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path


TIMEOUT_SECONDS = 15


def request(base_url, path, method="GET", token=None, body=None):
  headers = {"Accept": "application/json"}
  data = None
  if body is not None:
    headers["Content-Type"] = "application/json"
    data = body.encode("utf-8")
  if token:
    headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

  value = urllib.request.Request(
    f"{base_url.rstrip('/')}{path}",
    data=data,
    headers=headers,
    method=method,
  )

  try:
    with urllib.request.urlopen(
      value,
      timeout=TIMEOUT_SECONDS,
      context=ssl.create_default_context(),
    ) as response:
      return response.status, dict(response.headers), response.read().decode("utf-8")
  except urllib.error.HTTPError as error:
    return error.code, dict(error.headers), error.read().decode("utf-8")


def check(results, name, condition, evidence):
  results.append({"check": name, "passed": bool(condition), "evidence": evidence})


def scan(base_url, user_token=None, other_user_token=None, license_id=None):
  results = []

  status, headers, _ = request(base_url, "/health")
  check(results, "health endpoint", status == 200, f"status={status}")
  normalized = {key.lower(): value for key, value in headers.items()}
  check(
    results,
    "HSTS header",
    "strict-transport-security" in normalized,
    "header present/absent",
  )
  check(
    results,
    "anti-sniffing header",
    normalized.get("x-content-type-options", "").lower() == "nosniff",
    normalized.get("x-content-type-options", "missing"),
  )
  check(
    results,
    "no-store cache policy",
    normalized.get("cache-control", "").lower() == "no-store",
    normalized.get("cache-control", "missing"),
  )

  status, _, _ = request(base_url, "/licenses", method="POST", body="{}")
  check(
    results,
    "protected endpoint rejects anonymous access",
    status in {401, 403},
    f"status={status}",
  )

  if user_token:
    status, _, _ = request(
      base_url,
      "/licenses",
      method="POST",
      token=user_token,
      body="{",
    )
    check(results, "malformed JSON rejected", status == 400, f"status={status}")

    status, _, _ = request(
      base_url,
      "/licenses/not-a-uuid",
      token=user_token,
    )
    check(results, "invalid identifier rejected", status == 400, f"status={status}")

  if user_token and other_user_token and license_id:
    status, _, _ = request(
      base_url,
      f"/licenses/{license_id}",
      token=other_user_token,
    )
    check(results, "cross-owner BOLA defense", status == 404, f"status={status}")

  return results


def main():
  parser = argparse.ArgumentParser(description="Non-destructive DAST checks for a deployed lab API")
  parser.add_argument("--target", default=os.environ.get("TARGET_URL"))
  parser.add_argument("--user-token", default=os.environ.get("DAST_USER_TOKEN"))
  parser.add_argument("--other-user-token", default=os.environ.get("DAST_OTHER_USER_TOKEN"))
  parser.add_argument("--license-id", default=os.environ.get("DAST_LICENSE_ID"))
  parser.add_argument("--output", type=Path, default=Path("reports/dast.json"))
  args = parser.parse_args()

  if not args.target or not args.target.lower().startswith("https://"):
    parser.error("--target must be an HTTPS URL")

  results = scan(args.target, args.user_token, args.other_user_token, args.license_id)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

  for result in results:
    state = "PASS" if result["passed"] else "FAIL"
    print(f"[{state}] {result['check']}: {result['evidence']}")

  return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
  sys.exit(main())
