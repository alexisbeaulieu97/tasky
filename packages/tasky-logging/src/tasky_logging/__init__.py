"""Pluggable logging infrastructure for Tasky.

This package provides a logging abstraction layer that allows swappable logging
backends while maintaining a consistent interface for consumer packages.
"""

import logging
from typing import Protocol, runtime_checkable

from tasky_logging.config import configure_logging


@runtime_checkable
class Logger(Protocol):
    """Protocol defining the logging interface.

    This protocol enables dependency injection and allows swapping logging
    implementations without changing consumer code.
    """

    def debug(self, msg: object, *args: object) -> None:
        """Log a debug message."""
        ...

    def info(self, msg: object, *args: object) -> None:
        """Log an info message."""
        ...

    def warning(self, msg: object, *args: object) -> None:
        """Log a warning message."""
        ...

    def error(self, msg: object, *args: object) -> None:
        """Log an error message."""
        ...

    def critical(self, msg: object, *args: object) -> None:
        """Log a critical message."""
        ...


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    The logger name is automatically prefixed with "tasky." to namespace all
    application logs. Multiple calls with the same name return references to
    the same underlying logger instance.

    Args:
        name: The name for the logger (will be prefixed with "tasky.")

    Returns:
        A logger instance conforming to the Logger protocol

    Example:
        >>> logger = get_logger("tasks.service")
        >>> logger.info("Task created")

    """
    return logging.getLogger(f"tasky.{name}")


__all__ = ["Logger", "configure_logging", "get_logger"]
