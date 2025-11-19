# Change: Structured Error Results

## Why

Currently, error handlers return plain strings (`str`) which couples error handling logic to CLI-specific formatting. This creates three problems:

1. **Multi-transport limitation**: Future MCP servers and APIs cannot serialize errors differently (JSON vs CLI text)
2. **Testing difficulty**: Tests must parse strings instead of asserting on structured fields
3. **Inconsistent metadata**: Exit codes are registered separately from messages/suggestions, making it hard to maintain consistency

The existing `ErrorHandler` protocol returns `str`, forcing all transports to use the same text format. This violates clean architecture principles where presentation should be decoupled from error handling logic.

## What Changes

Introduce a structured `ErrorResult` dataclass that separates error data from presentation:

1. **New `ErrorResult` dataclass**: Contains `message`, `suggestion`, `exit_code`, and optional `traceback`
2. **Update `ErrorHandler` protocol**: Return `ErrorResult` instead of `str`
3. **Update all error handlers**: Return structured results
4. **Update `ErrorDispatcher.dispatch()`**: Return `ErrorResult`
5. **Update CLI presentation layer**: Format `ErrorResult` for terminal output
6. **Add decorator integration test**: Validate end-to-end flow without mocks

**Benefits**:
- MCP servers can serialize errors as JSON: `{"error": message, "hint": suggestion, "code": exit_code}`
- Tests assert on fields: `assert result.exit_code == 1` instead of `assert "Error:" in output`
- Logging can extract structured data for analytics
- Exit codes and messages stay synchronized (single return value)

## Impact

- **Affected specs**: `cli-error-presentation` (MODIFIED: Error Handler Centralization requirement)
- **Affected code**:
  - `packages/tasky-cli/src/tasky_cli/error_dispatcher.py` (ErrorHandler protocol, ErrorDispatcher, all handlers)
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` (with_task_error_handling decorator)
  - `packages/tasky-cli/tests/test_error_dispatcher.py` (update assertions)
  - `packages/tasky-cli/tests/test_error_handling.py` (update integration tests)

- **Breaking change**: **NO** - Internal refactoring only. CLI output format unchanged, API remains internal to tasky-cli package.
- **Dependencies**: None - standalone refactoring
- **Enables**: Phase 8 MCP server error serialization, structured logging, cleaner tests
