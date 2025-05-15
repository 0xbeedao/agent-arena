import logging
from typing import Protocol

import structlog
from rich.logging import RichHandler
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.stdlib import ProcessorFormatter


class ILogger(Protocol):
    def bind(self, *args, **kwargs) -> "ILogger": ...
    def debug(self, *args, **kwargs) -> None: ...
    def info(self, *args, **kwargs) -> None: ...
    def warn(self, *args, **kwargs) -> None: ...
    def error(self, *args, **kwargs) -> None: ...
class LoggingService:

    def __init__(
        self, capture=False, prod=False, level="DEBUG", name="arena", logger_levels=None
    ):
        self.capture = capture
        self.name = name
        self.prod = prod
        self.level = level
        self.logger_levels = logger_levels or {}
        self._setup = False

    def setup_logging(self):
        if not self._setup:
            # override built-in logging, use simple message since structlog
            # will be formatting
            # Configure Rich for standard library logging
            logging.basicConfig(
                handlers=[RichHandler(rich_tracebacks=False, markup=True)],
                format="%(message)s",
                level=getattr(logging, self.level.upper()),
            )
            baserenderer = (
                JSONRenderer() if self.capture or self.prod else ConsoleRenderer()
            )
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
                # In development mode, use a renderer that works well with Rich
                mainrenderer = (
                    JSONRenderer() if self.prod else ConsoleRenderer(colors=False)
                )
                structlog.configure(
                    processors=[
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.add_log_level,
                        structlog.processors.StackInfoRenderer(),
                        structlog.dev.set_exc_info,
                        structlog.processors.TimeStamper(fmt="iso"),
                        mainrenderer,
                    ],
                    logger_factory=structlog.stdlib.LoggerFactory(),
                    wrapper_class=structlog.stdlib.BoundLogger,
                    cache_logger_on_first_use=True,
                )
            log = structlog.get_logger("structlog")
            log.info("Set up logging with structlog", app=self.name)
            # Configure Uvicorn loggers to use structlog
            uvicorn_logger = logging.getLogger("uvicorn")
            uvicorn_logger.handlers = []  # Clear default handlers
            handler = logging.StreamHandler()
            handler.setFormatter(ProcessorFormatter(processor=baserenderer))
            uvicorn_logger.addHandler(handler)
            uvicorn_logger.setLevel(getattr(logging, self.level.upper()))
            # Turn down logging for APScheduler to avoid excessive logs
            aps_logger = logging.getLogger("apscheduler")
            aps_logger.setLevel(logging.WARNING)

            # Configure logger levels for specific loggers (factory, service, controller, etc.)
            for logger_name, level in self.logger_levels.items():
                logger = logging.getLogger(logger_name)
                logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))
                log.debug(f"Set logger '{logger_name}' to level {level}")

            # Optionally clear handlers to avoid duplicate output
            # if aps_logger.handlers:
            #    aps_logger.handlers = []
            self._setup = True

    def get_logger(self, *args, **kwargs) -> ILogger:
        """
        Get a Logging instance
        """
        self.setup_logging()
        return structlog.get_logger(*args, app=self.name, **kwargs)
