"""Automation hooks and shared lifecycle contracts for tasky."""

from tasky_hooks.errors import (
    ErrorResult,
    format_error_for_cli,
    log_fields_for_error,
    serialize_error_for_mcp,
)

__all__ = [
    "ErrorResult",
    "format_error_for_cli",
    "log_fields_for_error",
    "serialize_error_for_mcp",
]
