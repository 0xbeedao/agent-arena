from fastapi import FastAPI, Request
from structlog import get_logger
from asgi_correlation_id import CorrelationIdMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars
import time
from ulid import ULID

from agentarena.factories.logger_factory import LoggingService


class StructLogMiddleware(BaseHTTPMiddleware):
    """
    Adds threadlocal request ID to all logs, and tracks the time to complete.
    """

    async def dispatch(self, request: Request, call_next):
        clear_contextvars()  # Clear previous context
        bind_contextvars(request_id=request.headers.get("X-Correlation-ID", ULID().hex))
        log = get_logger("logging_middleware")
        start_time = time.perf_counter_ns()
        response = await call_next(request)
        duration = (time.perf_counter_ns() - start_time) / 1_000_000
        log.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )
        return response


def add_logging_middleware(app: FastAPI):
    app.add_middleware(CorrelationIdMiddleware)  # Add before StructLogMiddleware
    app.add_middleware(StructLogMiddleware)
