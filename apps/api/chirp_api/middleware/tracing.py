"""Request-level tracing and structured logging for Chirp API.

ISSUE 3 - Error Handling & Observability fix.
"""
import logging
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator

import grpc

_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = logging.getLogger("chirp_api")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [trace=%(trace_id)s method=%(method)s] %(message)s"
        )
    )
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


class TraceLoggerAdapter(logging.LoggerAdapter):
    """Injects trace_id and method into every log record."""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.get("extra", {})
        extra.setdefault("trace_id", get_trace_id() or "-")
        extra.setdefault("method", self.extra.get("method", "-"))
        kwargs["extra"] = extra
        return msg, kwargs


def get_trace_id() -> str:
    """Return the trace ID for the current request context."""
    return _trace_id_var.get("")


@contextmanager
def request_trace(
    method_name: str, user_id: str | None = None
) -> Generator[TraceLoggerAdapter, None, None]:
    """Context manager that sets a UUID trace ID for a gRPC call."""
    trace_id = str(uuid.uuid4())
    token = _trace_id_var.set(trace_id)
    log = TraceLoggerAdapter(logger, {"method": method_name})
    start = time.monotonic()
    log.info(
        "request started",
        extra={"trace_id": trace_id, "method": method_name, "user_id": user_id or "-"},
    )
    try:
        yield log
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        log.info(
            f"request completed in {elapsed_ms:.1f}ms",
            extra={"trace_id": trace_id, "method": method_name},
        )
        _trace_id_var.reset(token)


# Maps exception message patterns to gRPC status codes.
_ERROR_MAP = [
    ({"not found", "does not exist"}, grpc.StatusCode.NOT_FOUND),
    ({"already exists", "already taken", "duplicate"}, grpc.StatusCode.ALREADY_EXISTS),
    (
        {"authentication required", "invalid or expired", "unauthenticated"},
        grpc.StatusCode.UNAUTHENTICATED,
    ),
    (
        {"admin access required", "super admin", "not authorized", "permission denied"},
        grpc.StatusCode.PERMISSION_DENIED,
    ),
    (
        {"invalid", "required", "must be", "cannot", "too long", "characters or less"},
        grpc.StatusCode.INVALID_ARGUMENT,
    ),
    ({"banned"}, grpc.StatusCode.PERMISSION_DENIED),
]


def classify_error(error: Exception) -> grpc.StatusCode:
    """Map an exception to the most appropriate gRPC status code."""
    msg = str(error).lower()
    for keywords, code in _ERROR_MAP:
        if any(kw in msg for kw in keywords):
            return code
    return grpc.StatusCode.INTERNAL


def handle_grpc_error(
    error: Exception,
    context: grpc.ServicerContext,
    method_name: str,
    log: logging.LoggerAdapter | None = None,
) -> grpc.StatusCode:
    """Log and abort a gRPC call with the appropriate status code."""
    code = classify_error(error)
    _log = log or logger
    _log.error(
        f"gRPC error [{code.name}]: {error}",
        extra={
            "trace_id": get_trace_id(),
            "method": method_name,
            "grpc_code": code.name,
        },
    )
    context.abort(code, str(error))
    return code
