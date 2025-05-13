import time

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger
from structlog.contextvars import bind_contextvars
from structlog.contextvars import clear_contextvars
from ulid import ULID


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
