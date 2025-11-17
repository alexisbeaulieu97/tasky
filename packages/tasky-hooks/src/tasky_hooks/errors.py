"""Shared error contracts and formatting helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorResult:
    """Structured error information for multi-transport presentation."""

    message: str
    suggestion: str | None
    exit_code: int
    traceback: str | None = None

    def __post_init__(self) -> None:
        """Validate individual fields."""
        if self.exit_code <= 0:
            msg = f"exit_code must be > 0, got {self.exit_code}"
            raise ValueError(msg)
        if not self.message.strip():
            msg = "message must not be empty"
            raise ValueError(msg)


def format_error_for_cli(result: ErrorResult) -> str:
    """Render a CLI-friendly message."""
    parts = [f"Error: {result.message}"]
    if result.suggestion:
        parts.append(f"Suggestion: {result.suggestion}")
    if result.traceback:
        parts.append("")
        parts.append(result.traceback)
    return "\n".join(parts)


def serialize_error_for_mcp(result: ErrorResult) -> str:
    """Serialize an error for MCP transports."""
    payload = {
        "error": result.message,
        "hint": result.suggestion,
        "code": result.exit_code,
    }
    if result.traceback:
        payload["traceback"] = result.traceback
    return json.dumps(payload)


def log_fields_for_error(result: ErrorResult) -> dict[str, object]:
    """Return structured fields suitable for logging."""
    fields: dict[str, object] = {
        "level": "error",
        "message": result.message,
        "exit_code": result.exit_code,
    }
    if result.suggestion:
        fields["suggestion"] = result.suggestion
    if result.traceback:
        fields["traceback"] = result.traceback
    return fields
