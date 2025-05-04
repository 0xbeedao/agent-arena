import logging

import structlog

_SETUP = False


def setup_logging():
    global _SETUP
    if not _SETUP:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
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
        _SETUP = True


def get_logger(*args, **kwargs):
    """
    Get a Logging instance
    """

    return structlog.get_logger(*args, **kwargs)
