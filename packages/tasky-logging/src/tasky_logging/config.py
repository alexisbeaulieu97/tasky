"""Logging configuration module.

Provides functions for configuring the logging system based on settings.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tasky_settings.models import LoggingSettings


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def _get_log_level(verbosity: int) -> int:
    """Map verbosity level to logging level constant.

    Args:
        verbosity: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)

    Returns:
        Logging level constant from logging module

    """
    if verbosity == 0:
        return logging.WARNING
    if verbosity == 1:
        return logging.INFO
    return logging.DEBUG


def _get_formatter(format_style: str) -> logging.Formatter:
    """Create formatter based on format style.

    Args:
        format_style: Format style ("standard", "minimal", "json")

    Returns:
        Configured logging formatter

    """
    if format_style == "minimal":
        return logging.Formatter(fmt="%(levelname)s - %(message)s")
    if format_style == "json":
        return JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    # Default to standard for unknown or "standard"
    return logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_logging(settings: LoggingSettings) -> None:
    """Configure the logging system from settings.

    Sets up the root tasky logger with appropriate handlers, formatters,
    and log levels based on the settings object.

    Args:
        settings: LoggingSettings object containing verbosity and format configuration

    Example:
        >>> from tasky_settings import LoggingSettings
        >>> settings = LoggingSettings(verbosity=1, format="standard")
        >>> configure_logging(settings)
        >>> # Logs INFO and above messages

    """
    level = _get_log_level(settings.verbosity)

    # Get or create the root tasky logger
    logger = logging.getLogger("tasky")
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler with formatter
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(_get_formatter(settings.format))

    logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate messages
    logger.propagate = False


__all__ = ["configure_logging"]
