"""
Logging configuration for the CCDI Federation Service.

This module sets up structured logging using structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import get_settings


def configure_logging() -> FilteringBoundLogger:
    """Configure structured logging with structlog."""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
            if settings.log_format.lower() == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = None) -> FilteringBoundLogger:
    """Get a logger instance with optional name."""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def add_request_context(logger: FilteringBoundLogger, **context: Any) -> FilteringBoundLogger:
    """Add request context to logger."""
    return logger.bind(**context)
