from dataclasses import dataclass

from secure_api.errors import ApiError


@dataclass(frozen=True)
class Principal:
  subject: str
  username: str
  groups: frozenset

  @property
  def is_admin(self):
    return "admin" in self.groups


def principal_from_event(event):
  claims = (
    event.get("requestContext", {})
    .get("authorizer", {})
    .get("claims", {})
  )
  subject = claims.get("sub")
  if not subject:
    raise ApiError(401, "unauthorized", "Authentication is required")

  raw_groups = claims.get("cognito:groups", "")
  if isinstance(raw_groups, str):
    groups = frozenset(item.strip() for item in raw_groups.split(",") if item.strip())
  elif isinstance(raw_groups, list):
    groups = frozenset(str(item) for item in raw_groups)
  else:
    groups = frozenset()

  username = claims.get("cognito:username") or claims.get("email") or subject

  return Principal(subject=subject, username=username, groups=groups)
