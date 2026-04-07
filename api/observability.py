from __future__ import annotations

import contextvars
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any


_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """
    Configure process-wide structured logging once.
    """
    root = logging.getLogger()
    if getattr(root, "_pulseiq_logging_configured", False):
        return

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    setattr(root, "_pulseiq_logging_configured", True)


def set_request_id(request_id: str) -> contextvars.Token[str | None]:
    return _request_id_ctx.set(request_id)


def clear_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id_ctx.reset(token)


def get_request_id() -> str | None:
    return _request_id_ctx.get()

