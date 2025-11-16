# Tasks: Split Tasks CLI Module

## Phase 1: Create Module Structure (Non-breaking)

### Task 1.1: Create tasks module directory and __init__.py
- Create `packages/tasky-cli/src/tasky_cli/commands/tasks/` directory
- Create `__init__.py` with public API export:
  ```python
  """Task management commands for Tasky CLI."""
  from tasky_cli.commands.tasks.commands import task_app
  __all__ = ["task_app"]
  ```
- **Acceptance**: Directory exists with __init__.py exporting task_app

### Task 1.2: Verify module can be imported from CLI
- Update `packages/tasky-cli/src/tasky_cli/commands/__init__.py` to import from tasks module instead of tasks.py
- Run `uv run pytest` to verify zero test failures
- **Acceptance**: CLI can import task_app from tasks module; all tests pass

## Phase 2: Extract Validation Module

### Task 2.1: Create validation.py with input validation helpers
- Create `packages/tasky-cli/src/tasky_cli/commands/tasks/validation.py`
- Move validation functions from tasks.py:
  - `parse_task_id(task_id_str: str) -> UUID`
  - `parse_date_option(date_str: str, *, inclusive_end: bool) -> datetime`
  - `is_valid_date_format(date_str: str) -> bool`
  - `validate_status_option(status_str: str) -> list[TaskStatus] | None`
  - `parse_task_id_and_get_service(task_id: str) -> tuple[TaskService, UUID]`
  - `validate_name_not_empty(name: str) -> None`
  - `validate_import_strategy(strategy: str) -> None`
- Add comprehensive module docstring
- **Acceptance**: All validation functions in validation.py with proper type hints and docstrings

### Task 2.2: Consolidate duplicate date parsing logic
- Merge `_parse_created_after` and `_parse_created_before` into single `parse_date_option()`
- Use `inclusive_end` parameter to control end-of-day handling
- **Acceptance**: Single date parsing function handles both use cases

### Task 2.3: Update imports in tasks.py
- Add imports from validation module in tasks.py
- Remove original validation function definitions from tasks.py
- **Acceptance**: tasks.py imports from validation.py; zero import errors

### Task 2.4: Run tests and verify behavioral equivalence
- Run `uv run pytest`
- Verify all tests pass with zero changes to test files
- **Acceptance**: 577 tests pass; output/error messages unchanged

## Phase 3: Extract Formatting Module

### Task 3.1: Create formatting.py with output rendering helpers
- Create `packages/tasky-cli/src/tasky_cli/commands/tasks/formatting.py`
- Move formatting functions from tasks.py:
  - `get_status_indicator(status: TaskStatus) -> str`
  - `render_task_list(tasks, *, show_id, show_status, ...) -> None`
  - `render_task_detail(task: Task) -> None`
  - `render_list_summary(tasks, filter) -> None`
  - `render_import_result(result: ImportResult) -> None`
- Add comprehensive module docstring
- **Acceptance**: All formatting functions in formatting.py with clear responsibilities

### Task 3.2: Update imports in tasks.py
- Add imports from formatting module in tasks.py
- Remove original formatting function definitions from tasks.py
- **Acceptance**: tasks.py imports from formatting.py; zero import errors

### Task 3.3: Run tests and verify behavioral equivalence
- Run `uv run pytest`
- Verify all tests pass with zero changes to test files
- **Acceptance**: 577 tests pass; output format unchanged

## Phase 4: Extract Error Handling Module

### Task 4.1: Create error_handling.py with exception handlers
- Create `packages/tasky-cli/src/tasky_cli/commands/tasks/error_handling.py`
- Move error handling components from tasks.py:
  - `Handler` protocol
  - `with_task_error_handling` decorator
  - `render_error(message, suggestion, *, verbose, exc)` function
  - `dispatch_exception(exc, *, verbose)` function
  - `route_exception_to_handler(exc, *, verbose)` function
  - All handler functions (11 total):
    - `handle_task_domain_error`
    - `handle_task_not_found`
    - `handle_task_validation_error`
    - `handle_invalid_transition`
    - `handle_import_format_error`
    - `handle_import_export_error`
    - `handle_storage_error`
    - `handle_project_not_found_error`
    - `handle_backend_not_registered_error`
  - `suggest_transition(status)` helper
- Add comprehensive module docstring
- **Acceptance**: All error handling logic in error_handling.py with proper error routing

### Task 4.2: Update imports in tasks.py
- Add imports from error_handling module in tasks.py
- Remove original error handling definitions from tasks.py
- **Acceptance**: tasks.py imports decorator and handlers from error_handling.py

### Task 4.3: Run tests and verify behavioral equivalence
- Run `uv run pytest`
- Verify all tests pass with zero changes to test files
- Verify error messages and exit codes unchanged
- **Acceptance**: 577 tests pass; error handling behavior unchanged

## Phase 5: Finalize Commands Module

### Task 5.1: Rename tasks.py to commands.py
- Rename `packages/tasky-cli/src/tasky_cli/commands/tasks.py` to `packages/tasky-cli/src/tasky_cli/commands/tasks/commands.py`
- Clean up remaining imports
- Verify module contains only command definitions and orchestration logic
- **Acceptance**: commands.py exists in tasks/ directory with clean imports

### Task 5.2: Verify module sizes meet constraints
- Check each module is <400 lines:
  - `__init__.py`: ~10 lines
  - `commands.py`: <400 lines
  - `error_handling.py`: <250 lines
  - `formatting.py`: <150 lines
  - `validation.py`: <150 lines
- **Acceptance**: All modules meet size constraints

### Task 5.3: Remove complexity suppressions
- Remove `noqa: C901`, `noqa: PLR0912`, `noqa: PLR0915` from commands.py
- Run `uv run ruff check` to verify zero complexity warnings
- **Acceptance**: Zero complexity warnings in any module

### Task 5.4: Run final validation suite
- Run `uv run pytest` (verify 577 tests pass)
- Run `uv run ruff check --fix` (verify zero errors)
- Run `uv run pyright` (verify zero type errors)
- Run `uv run pytest --cov=packages/tasky-cli --cov-fail-under=80` (verify coverage maintained)
- **Acceptance**: All quality checks pass

## Phase 6: Add Module-Level Tests

### Task 6.1: Create unit tests for validation module
- Create `packages/tasky-cli/tests/commands/tasks/test_validation.py`
- Add tests for edge cases:
  - Invalid UUIDs (malformed strings, non-UUID values)
  - Invalid date formats (non-ISO 8601, malformed dates)
  - Boundary dates (timezone handling, start/end of day)
  - Empty/None inputs
  - Status validation (valid statuses, invalid statuses)
- **Acceptance**: Comprehensive validation tests covering edge cases

### Task 6.2: Create unit tests for formatting module
- Create `packages/tasky-cli/tests/commands/tasks/test_formatting.py`
- Add tests for output rendering:
  - Status indicators for all states (pending, completed, cancelled)
  - Task list with various flag combinations (show_id, show_status)
  - Summary message formatting (various task counts and filters)
  - Detail view rendering
- **Acceptance**: Comprehensive formatting tests covering output variations

### Task 6.3: Create unit tests for error handling module
- Create `packages/tasky-cli/tests/commands/tasks/test_error_handling.py`
- Add tests for error routing:
  - Each exception type routes to correct handler
  - Verbose mode shows stack trace
  - Non-verbose mode shows user-friendly message
  - Exit codes are correct for each error type
  - State transition suggestions work correctly
- **Acceptance**: Comprehensive error handling tests covering all paths

### Task 6.4: Verify coverage meets threshold
- Run `uv run pytest --cov=packages/tasky-cli --cov-report=term-missing`
- Verify new module tests increase coverage
- Verify coverage ≥80% threshold maintained
- **Acceptance**: Coverage ≥80% with new tests included

## Phase 7: Documentation and Finalization

### Task 7.1: Update module docstrings
- Add comprehensive docstrings to each module explaining:
  - Module purpose and responsibility
  - Key functions and their usage
  - Dependencies on other modules
  - Examples where appropriate
- **Acceptance**: All modules have clear, comprehensive docstrings

### Task 7.2: Update architecture documentation
- Update project documentation to reflect new module structure
- Add notes about module boundaries and responsibilities
- Document import patterns for future contributors
- **Acceptance**: Documentation reflects current modular structure

### Task 7.3: Final verification
- Run complete test suite: `uv run pytest`
- Run linting: `uv run ruff check --fix`
- Run type checking: `uv run pyright`
- Run coverage: `uv run pytest --cov=packages --cov-fail-under=80`
- Verify zero complexity warnings in any module
- **Acceptance**: All quality checks pass; ready for review
