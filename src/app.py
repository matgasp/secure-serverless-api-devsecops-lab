import os

from secure_api.handler import Api
from secure_api.repository import DynamoLicenseRepository


_api = None


def lambda_handler(event, context):
  global _api

  if _api is None:
    table_name = os.environ.get("LICENSES_TABLE", "")
    if not table_name:
      raise RuntimeError("LICENSES_TABLE is not configured")

    _api = Api(DynamoLicenseRepository(table_name))

  return _api.handle(event, context)
