"""Structured fields go in `extra=fields(...)`; the JSON and text formatters both render them."""

import json
import logging
import re
import sys
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, Literal

LogFormat = Literal["text", "json"]

# Set per HTTP request by RequestContextMiddleware. asyncio copies context into the tasks the
# graph spawns, so log lines from every node of an analysis carry the same ID.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_CLIENT_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

# Uvicorn logs its general server messages (startup, shutdown, reloads) under "uvicorn.error",
# a historical name kept for compatibility; show it as what it is.
_DISPLAY_NAMES = {"uvicorn.error": "uvicorn"}


def new_request_id(incoming: str | None = None) -> str:
    """Reuse a well-formed ID from the caller (e.g. a proxy's X-Request-ID), else mint one."""
    if incoming and _CLIENT_REQUEST_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex[:16]


def current_request_id() -> str | None:
    return request_id_var.get()


def fields(**values: Any) -> dict[str, Any]:
    return {"fields": values}


class _ContextFilter(logging.Filter):
    """Adds the request ID and tidies logger names, for both formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.name = _DISPLAY_NAMES.get(record.name, record.name)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if request_id := getattr(record, "request_id", None):
            entry["request_id"] = request_id
        entry.update(getattr(record, "fields", None) or {})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(name)s%(request)s: %(message)s%(details)s")

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None)
        record.request = f" [{request_id}]" if request_id else ""
        values = getattr(record, "fields", None) or {}
        record.details = "".join(f" {key}={_text_value(value)}" for key, value in values.items())
        return super().format(record)


def _text_value(value: Any) -> str:
    if isinstance(value, dict):
        return ",".join(f"{k}:{v}" for k, v in value.items()) or "-"
    text = str(value)
    return json.dumps(text) if " " in text else text


def configure_logging(level: str = "INFO", log_format: LogFormat = "text") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if log_format == "json" else TextFormatter())
    handler.addFilter(_ContextFilter())

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # Uvicorn's loggers propagate to ours, so their lines get the same format. Its access log is
    # silenced: RequestContextMiddleware logs every request with its ID and full duration instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # Per-request noise from the HTTP stack; our own upstream logging covers what matters.
    for name in ("httpx", "httpcore", "httpx2", "openai"):
        logging.getLogger(name).setLevel(logging.WARNING)
