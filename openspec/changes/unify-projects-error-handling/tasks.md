# Tasks: Unify Projects Error Handling

## Phase 1: Add Error Handling Infrastructure

### Task 1.1: Add Handler protocol and type definitions
- Open `packages/tasky-cli/src/tasky_cli/commands/projects.py`
- Add import: `from typing import Protocol, Callable, Any`
- Add import: `import functools`
- Add import: `import traceback`
- Add `Handler` protocol definition
- **Acceptance**: Handler protocol defined with proper type hints

### Task 1.2: Implement render_error function
- Add `_render_error(message, suggestion, *, verbose, exc)` function
- Implement error message formatting to stderr
- Implement optional suggestion output
- Implement verbose mode stack trace output
- Add comprehensive docstring
- **Acceptance**: Function renders errors consistently with proper formatting

### Task 1.3: Implement exception routing functions
- Add `_route_exception_to_handler(exc, *, verbose)` function
- Add necessary imports for exception types:
  - `from tasky_projects.errors import ProjectNotFoundError`
  - `from tasky_settings.errors import BackendNotRegisteredError`
  - `from tasky_storage.errors import StorageError`
- Implement routing logic based on exception type
- Add `_dispatch_exception(exc, *, verbose)` function
- **Acceptance**: Routing functions correctly map exceptions to handlers

### Task 1.4: Implement specialized error handlers
- Add `_handle_project_not_found(exc, *, verbose)` handler
- Add `_handle_backend_not_registered(exc, *, verbose)` handler
- Add `_handle_storage_error(exc, *, verbose)` handler
- Add `_handle_validation_error(exc, *, verbose)` handler
- Add `_handle_generic_error(exc, *, verbose)` handler
- Each handler SHALL call `_render_error()` with appropriate message and suggestion
- Each handler SHALL raise `typer.Exit` with correct exit code
- **Acceptance**: 5 specialized handlers implemented with contextual suggestions

### Task 1.5: Implement with_project_error_handling decorator
- Add `with_project_error_handling(func)` decorator function
- Decorator wraps command functions to catch exceptions
- Decorator passes through `typer.Exit` without handling
- Decorator extracts `verbose` flag from kwargs
- Decorator calls `_dispatch_exception()` for all other exceptions
- **Acceptance**: Decorator correctly wraps functions and routes exceptions

### Task 1.6: Verify module still loads and runs
- Run `uv run python -c "from tasky_cli.commands.projects import project_app"`
- Verify no import errors
- Verify existing commands still work (before refactoring)
- **Acceptance**: Module loads successfully; existing behavior unchanged

## Phase 2: Refactor Commands

### Task 2.1: Refactor init_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed error information")` parameter
- Remove try/except block around backend validation (lines 17-23)
- Remove try/except block around config loading (lines 40-46)
- Move command logic to top level (no try/except wrapper)
- Run `uv run pytest packages/tasky-cli/tests/ -k init -v`
- **Acceptance**: init_command uses decorator; tests pass; error behavior improved

### Task 2.2: Refactor info_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool` parameter
- Remove try/except blocks (lines 76-99, 112-118)
- Move command logic to top level
- Run `uv run pytest packages/tasky-cli/tests/ -k info -v`
- **Acceptance**: info_command uses decorator; tests pass

### Task 2.3: Refactor register_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool` parameter
- Remove try/except blocks (lines 272-287)
- Move command logic to top level
- Run `uv run pytest packages/tasky-cli/tests/ -k register -v`
- **Acceptance**: register_command uses decorator; tests pass

### Task 2.4: Refactor unregister_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool` parameter
- Remove try/except blocks (lines 300-330)
- Move command logic to top level
- Run `uv run pytest packages/tasky-cli/tests/ -k unregister -v`
- **Acceptance**: unregister_command uses decorator; tests pass

### Task 2.5: Refactor discover_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool` parameter
- Remove try/except blocks (lines 348-395)
- Move command logic to top level
- Run `uv run pytest packages/tasky-cli/tests/ -k discover -v`
- **Acceptance**: discover_command uses decorator; tests pass

### Task 2.6: Refactor list_command
- Add `@with_project_error_handling` decorator
- Add `verbose: bool` parameter
- Remove try/except blocks (lines 154-248)
- Move command logic to top level
- Verify clean flag logic still works correctly
- Run `uv run pytest packages/tasky-cli/tests/ -k list -v`
- **Acceptance**: list_command uses decorator; tests pass; clean logic preserved

## Phase 3: Code Quality Improvements

### Task 3.1: Remove noqa suppressions
- Remove all `# noqa: BLE001` suppressions (now unnecessary)
- Remove all `# noqa: C901` suppressions that are no longer needed
- Remove all `# noqa: TRY301` suppressions (decorator handles this)
- **Acceptance**: All appropriate noqa suppressions removed

### Task 3.2: Run linting and type checking
- Run `uv run ruff check packages/tasky-cli/src/tasky_cli/commands/projects.py`
- Fix any linting issues
- Run `uv run pyright packages/tasky-cli/src/tasky_cli/commands/projects.py`
- Fix any type errors
- **Acceptance**: Zero linting or type errors

### Task 3.3: Verify line count reduction
- Check git diff for projects.py
- Verify net line reduction (removing 8 try/except blocks, adding shared handlers)
- Expected: ~30-40 line reduction
- **Acceptance**: Code is more concise; duplication removed

## Phase 4: Testing

### Task 4.1: Run full test suite
- Run `uv run pytest packages/tasky-cli/tests/ -v`
- Verify all tests pass
- Verify zero new test failures
- **Acceptance**: Complete test suite passes

### Task 4.2: Add verbose mode tests
- Create test cases for verbose mode in project commands
- Test that `--verbose` flag shows stack trace on errors
- Test that non-verbose mode shows clean errors
- **Acceptance**: Verbose mode tests cover error scenarios

### Task 4.3: Add exception routing tests
- Create test cases for each exception type
- Verify ProjectNotFoundError shows "Run 'tasky project list'" suggestion
- Verify BackendNotRegisteredError shows available backends
- Verify StorageError exits with code 3
- Verify ValueError/TypeError handled as validation errors
- **Acceptance**: Exception routing tests verify correct handler selection

### Task 4.4: Verify error message improvements
- Manually test common error scenarios
- Verify error messages are consistent and helpful
- Verify suggestions are actionable
- Compare with tasks.py error messages for consistency
- **Acceptance**: Error messages match quality of tasks.py patterns

## Phase 5: Documentation

### Task 5.1: Update command help text
- Ensure all commands document `--verbose` flag in help
- Verify help text is consistent across commands
- Run `uv run tasky project --help` to verify
- **Acceptance**: Help text documents verbose mode

### Task 5.2: Add module docstring updates
- Update projects.py module docstring to document error handling pattern
- Document error handler infrastructure for future contributors
- **Acceptance**: Module documentation reflects new error handling approach

### Task 5.3: Final verification
- Run complete validation suite:
  - `uv run pytest`
  - `uv run ruff check --fix`
  - `uv run pyright`
  - `uv run pytest --cov=packages --cov-fail-under=80`
- Verify all quality checks pass
- **Acceptance**: All quality gates passed; ready for review
