# Implementation Tasks

## 1. Core Infrastructure

- [ ] 1.1 Define `ErrorResult` dataclass in `error_dispatcher.py`
  - Fields: `message: str`, `suggestion: str | None`, `exit_code: int`, `traceback: str | None`
  - Include docstring explaining field purposes
  - Add `__post_init__` validation (exit_code > 0, message non-empty)

- [ ] 1.2 Update `ErrorHandler` protocol signature
  - Change return type from `str` to `ErrorResult`
  - Update protocol docstring to explain structured results

- [ ] 1.3 Update `ErrorDispatcher.dispatch()` method
  - Change return type from `str` to `ErrorResult`
  - Update docstring and type hints

## 2. Update Error Handlers (10 handlers)

- [ ] 2.1 Update `_handle_task_not_found` to return `ErrorResult`
  - Extract message, suggestion, exit_code from current implementation
  - Return `ErrorResult(message=..., suggestion=..., exit_code=1, traceback=...)`

- [ ] 2.2 Update `_handle_task_validation_error` to return `ErrorResult`

- [ ] 2.3 Update `_handle_invalid_transition` to return `ErrorResult`

- [ ] 2.4 Update `_handle_invalid_export_format_error` to return `ErrorResult`

- [ ] 2.5 Update `_handle_incompatible_version_error` to return `ErrorResult`

- [ ] 2.6 Update `_handle_export_error` to return `ErrorResult`

- [ ] 2.7 Update `_handle_import_error` to return `ErrorResult`

- [ ] 2.8 Update `_handle_generic_task_domain_error` to return `ErrorResult`

- [ ] 2.9 Update `_handle_storage_error` to return `ErrorResult`

- [ ] 2.10 Update `_handle_project_not_found` to return `ErrorResult`

- [ ] 2.11 Update `_handle_backend_not_registered` to return `ErrorResult`

- [ ] 2.12 Update `_handle_pydantic_validation_error` to return `ErrorResult`

- [ ] 2.13 Update `_handle_unexpected_error` to return `ErrorResult` (exit_code=2)

- [ ] 2.14 Update `_format_error` helper to build and return `ErrorResult`

## 3. Update CLI Presentation Layer

- [ ] 3.1 Update `with_task_error_handling` decorator in `tasks.py`
  - Receive `ErrorResult` from `dispatcher.dispatch()`
  - Format result for CLI: `f"{result.message}\n{result.suggestion or ''}"`
  - Extract `exit_code` from result instead of dispatcher property
  - Remove `dispatcher.exit_code` property access

- [ ] 3.2 Add `_format_error_for_cli(result: ErrorResult) -> str` helper
  - Build CLI output: "Error: {message}\nSuggestion: {suggestion}" format
  - Include traceback if `result.traceback` is present
  - Return formatted string for `typer.echo()`

## 4. Update Tests

- [ ] 4.1 Update `test_error_dispatcher.py` unit tests
  - Change assertions from string matching to `ErrorResult` field checks
  - Example: `assert result.message == "Task 'abc' not found"` instead of `assert "Task 'abc' not found" in message`
  - Update all 16 test methods

- [ ] 4.2 Update `test_error_handling.py` integration tests
  - CLI output format unchanged, so stderr assertions remain the same
  - Verify exit codes still correct

- [ ] 4.3 Add decorator integration test (new)
  - Create temporary test command with `@with_task_error_handling`
  - Raise `TaskNotFoundError` and verify:
    - Exit code propagated correctly
    - Error message formatted correctly
    - Verbose flag reads from context
  - Test without mocking internals (full decorator path)

## 5. Documentation & Validation

- [ ] 5.1 Update docstrings for `ErrorResult`, `ErrorHandler`, `ErrorDispatcher`

- [ ] 5.2 Run test suite and verify all tests pass
  - `uv run pytest packages/tasky-cli/tests/test_error_dispatcher.py -v`
  - `uv run pytest packages/tasky-cli/tests/test_error_handling.py -v`

- [ ] 5.3 Run type checker and verify no errors
  - `uv run pyright packages/tasky-cli/src/tasky_cli/error_dispatcher.py`
  - `uv run pyright packages/tasky-cli/src/tasky_cli/commands/tasks.py`

- [ ] 5.4 Run linter and fix any issues
  - `uv run ruff check packages/tasky-cli --fix`

- [ ] 5.5 Verify CLI behavior unchanged (manual smoke test)
  - `uv run tasky task show invalid-uuid` (should show friendly error)
  - `uv run tasky task list --verbose` (should work normally)
  - `uv run tasky task create` (should validate input)
