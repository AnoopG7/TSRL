import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

from config.settings import get_settings

settings = get_settings()


def setup_logging() -> None:
    log_dir = Path(settings.logging.output_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
            if settings.logging.format == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.logging.level)
        ),
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_context: Any):
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class LoggerMixin:
    @property
    def logger(self):
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(name)


setup_logging()
