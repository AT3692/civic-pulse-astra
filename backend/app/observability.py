import contextvars
import json
import logging
import sys
from datetime import UTC, datetime

from prometheus_client import Counter, Histogram

request_id = contextvars.ContextVar("request_id", default="-")
REQUESTS = Counter("civicpulse_http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("civicpulse_http_request_seconds", "HTTP latency", ["method", "route"])
TRIAGE = Histogram("civicpulse_triage_seconds", "Triage latency", ["provider"])
FALLBACKS = Counter("civicpulse_triage_fallback_total", "Provider fallbacks", ["provider"])


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id.get(),
        }
        for key in ("complaint_id", "provider", "error_class", "status", "route", "latency_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        # Deliberately exclude exception text: HTTP errors may embed credentials or PII.
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(handlers=[handler], level=level, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
