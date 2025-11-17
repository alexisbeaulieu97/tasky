"""MCP-specific error types and error handling."""

from __future__ import annotations

from tasky_tasks.exceptions import TaskDomainError


class MCPError(TaskDomainError):
    """Base class for MCP server errors."""


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
