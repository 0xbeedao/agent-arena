import logging
from typing import Protocol

import structlog


class ILogger(Protocol):
    def bind(self, *args, **kwargs) -> "ILogger": ...
    def debug(self, *args, **kwargs) -> None: ...
    def info(self, *args, **kwargs) -> None: ...
    def warn(self, *args, **kwargs) -> None: ...
    def error(self, *args, **kwargs) -> None: ...
class LoggingService:

    def __init__(self, capture=False):
        self.capture = capture
        self._setup = False

    def setup_logging(self):
        if not self._setup:
            if self.capture:
                cf = structlog.testing.CapturingLoggerFactory()
                structlog.configure(
                    logger_factory=cf,
                    processors=[
                        structlog.processors.add_log_level,
                        structlog.processors.JSONRenderer(),
                    ],
                )
            else:
                structlog.configure(
                    processors=[
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.add_log_level,
                        structlog.processors.StackInfoRenderer(),
                        structlog.dev.set_exc_info,
                        structlog.processors.TimeStamper(
                            fmt="%Y-%m-%d %H:%M:%S", utc=False
                        ),
                        structlog.dev.ConsoleRenderer(),
                    ],
                    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
                    context_class=dict,
                    logger_factory=structlog.PrintLoggerFactory(),
                    cache_logger_on_first_use=False,
                )
                structlog.get_logger("structlog", module="factories.logger").info(
                    "Set up logging with structlog"
                )
            self._setup = True

    def get_logger(self, *args, **kwargs) -> ILogger:
        """
        Get a Logging instance
        """
        self.setup_logging()
        return structlog.get_logger(*args, **kwargs)
