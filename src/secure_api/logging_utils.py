import json
import logging
import os


LOGGER = logging.getLogger("secure_api")
LOGGER.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


def log_event(level, event_name, **fields):
  record = {"event": event_name, **fields}
  message = json.dumps(record, separators=(",", ":"), sort_keys=True)

  getattr(LOGGER, level.lower(), LOGGER.info)(message)
