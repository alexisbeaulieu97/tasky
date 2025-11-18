"""MCP-specific error types and error handling."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from tasky_tasks.exceptions import TaskDomainError


class MCPError(TaskDomainError):
    """Base class for MCP server errors with structured suggestions."""

    def __init__(
        self,
        message: str,
        *,
        suggestions: Iterable[str] | Mapping[str, object] | str | None = None,
        **context: object,
    ) -> None:
        super().__init__(message, **context)
        # Normalize suggestions to a JSON-serializable structure for error payloads
        normalized: list[str] | dict[str, object] | None
        if suggestions is None:
            normalized = None
        elif isinstance(suggestions, Mapping):
            normalized = dict(suggestions)
        elif isinstance(suggestions, str):
            normalized = [suggestions]
        elif isinstance(suggestions, Iterable):
            normalized = [str(item) for item in suggestions]
        else:
            normalized = [str(suggestions)]
        self.suggestions = normalized


class MCPValidationError(MCPError):
    """Raised when MCP request validation fails."""


class MCPAuthenticationError(MCPError):
    """Raised when OAuth authentication fails."""


class MCPAuthorizationError(MCPError):
    """Raised when OAuth authorization (scope check) fails."""


class MCPTimeoutError(MCPError):
    """Raised when MCP request times out."""


class MCPConcurrencyError(MCPError):
    """Raised when concurrent request limit is exceeded."""


def map_domain_error_to_mcp(error: Exception) -> dict[str, str]:
    """Map domain exceptions to MCP error responses.

    Args:
        error: The exception to map

    Returns:
        Dictionary with 'code' and 'message' keys for MCP error response

    """
    error_map = {
        MCPValidationError: "validation_error",
        MCPAuthenticationError: "authentication_error",
        MCPAuthorizationError: "authorization_error",
        MCPTimeoutError: "timeout_error",
        MCPConcurrencyError: "concurrency_error",
        TaskDomainError: "task_error",
    }

    for error_type, code in error_map.items():
        if isinstance(error, error_type):
            return {"code": code, "message": str(error)}

    # Unknown error
    return {"code": "internal_error", "message": "An internal error occurred"}
