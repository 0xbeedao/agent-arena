import logging

import structlog


class LoggingService:

    def __init__(self):
        self._setup = False

    def setup_logging(self):
        if not self._setup:
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

    def get_logger(self, *args, **kwargs):
        """
        Get a Logging instance
        """
        self.setup_logging()
        return structlog.get_logger(*args, **kwargs)
