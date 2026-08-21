import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra"


def combined_terraform():
  return "\n".join(path.read_text(encoding="utf-8") for path in sorted(INFRA.glob("*.tf")))


def main():
  content = combined_terraform()
  required_controls = {
    "Python 3.14 Lambda runtime": 'runtime       = "python3.14"',
    "DynamoDB encryption": "server_side_encryption",
    "DynamoDB point-in-time recovery": "point_in_time_recovery",
    "Cognito authorization": 'authorization = "COGNITO_USER_POOLS"',
    "API throttling": "throttling_rate_limit",
    "Lambda reserved concurrency": "reserved_concurrent_executions",
    "API payload logging disabled": "data_trace_enabled     = false",
    "WAF rate-based rule": "rate_based_statement",
    "X-Ray tracing": 'mode = "Active"',
  }

  failures = [name for name, token in required_controls.items() if token not in content]

  forbidden = {
    "IAM wildcard action": re.compile(r"actions\s*=\s*\[\s*\"\*\"\s*\]"),
    "Public-read ACL": re.compile(r"acl\s*=\s*\"public-read"),
    "Unencrypted transport": re.compile(r"http://", re.IGNORECASE),
  }

  for name, pattern in forbidden.items():
    if pattern.search(content):
      failures.append(name)

  wildcard_resources = len(re.findall(r"resources\s*=\s*\[\s*\"\*\"\s*\]", content))
  if wildcard_resources != 1 or 'sid    = "WriteTraces"' not in content:
    failures.append("Unexpected IAM wildcard resource outside the documented X-Ray exception")

  if failures:
    print("IaC policy checks failed:")
    for failure in failures:
      print(f"- {failure}")

    return 1

  print("IaC policy checks passed.")

  return 0


if __name__ == "__main__":
  sys.exit(main())
