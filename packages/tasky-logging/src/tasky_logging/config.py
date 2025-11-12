"""Logging configuration module.

Provides functions for configuring the logging system based on CLI flags
or programmatic settings.
"""

import logging
import sys


def configure_logging(
    verbosity: int = 0,
    format_style: str = "standard",
) -> None:
    """Configure the logging system.

    Sets up the root tasky logger with appropriate handlers, formatters,
    and log levels based on the requested verbosity.

    Args:
        verbosity: Verbosity level (0=WARNING+, 1=INFO+, 2+=DEBUG+)
        format_style: Format style for log messages ("standard" supported)

    Example:
        >>> configure_logging(verbosity=1)
        >>> # Logs INFO and above messages

    """
    # Map verbosity to log level
    if verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:  # 2+
        level = logging.DEBUG

    # Get or create the root tasky logger
    logger = logging.getLogger("tasky")
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter based on style
    if format_style == "standard":
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Default to standard if unknown format requested
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate messages
    logger.propagate = False


__all__ = ["configure_logging"]
