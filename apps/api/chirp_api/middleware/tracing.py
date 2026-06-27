"""Request-level tracing and structured logging for Chirp API.

ISSUE 3 — Error Handling & Observability:

Problems identified:
  1. No request tracing: impossible to correlate logs to a single RPC call.
  2. Inconsistent error handling across handlers:
     - auth_handler.GetCurrentUser:  context.abort(UNAUTHENTICATED)
     - posts_handler.GetPost:        returns empty PostResponse (silent failure)
     - feed_handler.GetHomeFeed:     no try/except, raw exception propagates
     - admin_handler.ListUsers:      no try/except, raw exception propagates
     - posts_handler.CreatePost:     returns success=False with error string
     This mix of strategies makes clients and debuggers guess what happened.
  3. No structured log output: log lines lack context (method, trace ID, user).

Fix:
  - Each gRPC call generates a UUID trace_id on entry.
  - trace_id propagates through the service layer via a contextvars.ContextVar.
  - All log output includes trace_id, method name, and user_id where available.
  - A unified handle_error() function maps exception types to gRPC status codes
    and logs structured error records.
  - Handlers that previously returned silent empty responses now log the error
    with a trace_id so production issues are debuggable.
"""

import logging
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar

import grpc

# ContextVar for the current request's trace ID.
# Stored per-coroutine/thread; safe for concurrent requests.
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = logging.getLogger("chirp_api")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s "
            "[trace=%(trace_id)s method=%(method)s] %(message)s"
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class TraceLoggerAdapter(logging.LoggerAdapter):
    """Injects trace_id and method into every log record automatically."""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.setdefault("trace_id", get_trace_id() or "-")
        extra.setdefault("method", self.extra.get("method", "-"))
        kwargs["extra"] = extra
        return msg, kwargs


def get_trace_id() -> str:
    """Return the trace ID for the current request context."""
    return _trace_id_var.get("")


@contextmanager
def request_trace(method_name: str, user_id: str | None = None):
    """Context manager that sets a trace ID for the duration of a gRPC call.

    Logs request start and completion with timing. Yields a TraceLoggerAdapter
    pre-configured with trace_id and method name.
    """
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


# Error taxonomy: maps exception message patterns to gRPC status codes.
# Order matters: more specific patterns first.
_ERROR_MAP = [
    ({"not found", "does not exist"}, grpc.StatusCode.NOT_FOUND),
    ({"already exists", "already taken", "duplicate"}, grpc.StatusCode.ALREADY_EXISTS),
    ({"authentication required", "invalid or expired", "unauthenticated"}, grpc.StatusCode.UNAUTHENTICATED),
    ({"admin access required", "super admin", "not authorized", "permission denied"}, grpc.StatusCode.PERMISSION_DENIED),
    ({"invalid", "required", "must be", "cannot", "too long", "characters or less"}, grpc.StatusCode.INVALID_ARGUMENT),
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
    """Log and abort a gRPC call with the appropriate status code.

    Returns the status code for callers that need it.
    """
    code = classify_error(error)
    trace_id = get_trace_id()
    message = str(error)

    _log = log or logger
    _log.error(
        f"gRPC error [{code.name}]: {message}",
        extra={
            "trace_id": trace_id,
            "method": method_name,
            "grpc_code": code.name,
        },
    )

    context.abort(code, message)
    return code
