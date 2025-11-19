# cli-error-presentation Delta

## MODIFIED Requirements

### Requirement: Error Handler Centralization

The CLI SHALL implement error handling consistently across all commands, SHALL avoid duplicated error handling code, SHALL use decorators or context managers for common error patterns, and SHALL handle unexpected errors gracefully with a generic message. **Error handlers SHALL return structured `ErrorResult` objects containing message, suggestion, exit code, and optional traceback, enabling multi-transport presentation (CLI, MCP, API) without changing handler logic.**

#### Scenario: Consistent error handling

**Given** multiple CLI commands that perform task operations
**When** any command encounters a `TaskNotFoundError`
**Then** all commands SHALL present the error identically
**And** use the same exit code

#### Scenario: Unexpected error handling

**Given** an unexpected exception (not domain or storage)
**When** the CLI catches it
**Then** it SHALL display: "An unexpected error occurred"
**And** SHALL suggest filing a bug report
**And** SHALL exit with code 2

#### Scenario: Structured error results

**Given** an error handler processes any exception
**When** the handler completes processing
**Then** it SHALL return an `ErrorResult` object
**And** the result SHALL contain `message: str` (user-friendly error text)
**And** the result SHALL contain `suggestion: str | None` (optional actionable guidance)
**And** the result SHALL contain `exit_code: int` (1 for user errors, 2 for internal, 3 for storage)
**And** the result SHALL contain `traceback: str | None` (populated only if verbose mode enabled)

#### Scenario: Multi-transport presentation

**Given** an `ErrorResult` from the error dispatcher
**When** presenting to CLI
**Then** format as "Error: {message}\nSuggestion: {suggestion}" text
**When** presenting to MCP server
**Then** serialize as JSON `{"error": message, "hint": suggestion, "code": exit_code}`
**When** presenting to structured logs
**Then** extract fields for analytics: `{"level": "error", "message": message, "exit_code": exit_code}`

#### Scenario: Test assertions on structured data

**Given** a test for error handler behavior
**When** asserting the handler output
**Then** tests SHALL assert on `ErrorResult` fields directly
**And** avoid parsing string output
**Example**: `assert result.exit_code == 1` instead of `assert "Error:" in output`
