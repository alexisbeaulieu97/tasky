# Design: Split Tasks CLI Module

## Problem Analysis

### Current State
`tasks.py` (991 lines) contains:
- 13 command functions (create, list, show, update, complete, cancel, reopen, delete, import, export, etc.)
- 11 error handler functions (606-830)
- 8+ validation helpers (_is_valid_date_format, _parse_task_id_and_get_service, etc.)
- 3+ formatting helpers (_get_status_indicator, output rendering)
- 1 decorator (with_task_error_handling)
- Multiple protocols and type definitions

### Complexity Hotspots
1. **`list_command()`** (lines 132-323): 191 lines
   - Date parsing & validation (40 lines duplicated for created_after/created_before)
   - Filter construction
   - Sorting logic
   - Output rendering
   - Summary formatting

2. **Error handling block** (lines 606-830): 224 lines
   - 11 handler functions with nested conditionals
   - Routing logic (_route_exception_to_handler, _dispatch_exception)
   - Verbose mode handling

3. **Mixed responsibilities**: Commands call validation helpers which call service methods which may raise exceptions handled by handlers defined in same file

## Design Decision: Modular Structure

### Option 1: Flat Module with Sections (REJECTED)
Keep single file but organize into sections with comments.

**Pros**: Minimal refactoring
**Cons**: Still 991 lines; doesn't address complexity; organizational drift over time

### Option 2: Split into Module (SELECTED)
Create `tasks/` directory with focused modules.

**Pros**:
- Clear separation of concerns
- Easier to test components in isolation
- Supports future growth (new output formats, validators, handlers)
- Reduces cognitive load (each file <250 lines)

**Cons**:
- Initial refactoring effort
- More files to navigate (mitigated by clear naming)

## Module Design

### `tasks/__init__.py` (Public API)
**Responsibility**: Export public interface for tasky-cli app registration

```python
"""Task management commands for Tasky CLI."""

from tasky_cli.commands.tasks.commands import task_app

__all__ = ["task_app"]
```

**Size**: ~10 lines
**Dependencies**: commands module

---

### `tasks/commands.py` (Command Definitions)
**Responsibility**: Typer command definitions and orchestration

**Contents**:
- `task_app` (Typer app instance)
- Command functions: create_command, list_command, show_command, update_command, complete_command, cancel_command, reopen_command, delete_command
- Import/export commands
- Callback configuration
- Command orchestration logic (calls validation → service → formatting → error handling)

**Size**: ~350-400 lines
**Dependencies**: validation, formatting, error_handling modules; external (tasky_settings, tasky_tasks)

**Example**:
```python
@task_app.command("list")
@with_task_error_handling
def list_command(
    status: str | None = typer.Option(None, "--status", help="..."),
    search: str | None = typer.Option(None, "--search", help="..."),
    ...
) -> None:
    # Parse and validate inputs
    parsed_status = validate_status_option(status) if status else None
    created_after = parse_date_option(created_after_str, inclusive_end=False) if created_after_str else None

    # Get service and execute
    service = get_service()
    task_filter = TaskFilter(statuses=parsed_status, name_contains=search, ...)
    tasks = service.find_tasks(task_filter)

    # Format and display
    render_task_list(tasks, show_id=True, show_status=True)
    render_list_summary(tasks, task_filter)
```

---

### `tasks/error_handling.py` (Error Handling)
**Responsibility**: Exception handling, error rendering, error routing

**Contents**:
- `Handler` protocol
- `with_task_error_handling` decorator
- Error rendering: `render_error(message, suggestion, verbose, exc)`
- Error routing: `dispatch_exception(exc, verbose)`, `route_exception_to_handler(exc, verbose)`
- Handler functions:
  - `handle_task_domain_error`
  - `handle_task_not_found`
  - `handle_task_validation_error`
  - `handle_invalid_transition`
  - `handle_import_format_error`
  - `handle_import_export_error`
  - `handle_storage_error`
  - `handle_project_not_found_error`
  - `handle_backend_not_registered_error`
- Helper: `suggest_transition(status)` (state machine suggestions)

**Size**: ~250 lines
**Dependencies**: tasky_tasks exceptions, tasky_storage errors, tasky_settings exceptions

**Example**:
```python
def render_error(
    message: str,
    suggestion: str | None = None,
    *,
    verbose: bool,
    exc: Exception | None = None,
) -> None:
    """Render error message with optional suggestion and verbose details."""
    typer.echo(f"Error: {message}", err=True)
    if suggestion:
        typer.echo(f"Suggestion: {suggestion}", err=True)
    if verbose and exc:
        typer.echo("\nDetailed error:", err=True)
        typer.echo(traceback.format_exc(), err=True)
```

---

### `tasks/formatting.py` (Output Formatting)
**Responsibility**: Display logic, output rendering, status indicators

**Contents**:
- `get_status_indicator(status)` → emoji/symbol
- `render_task_list(tasks, show_id, show_status, ...)` → formatted list output
- `render_task_detail(task)` → single task detail view
- `render_list_summary(tasks, filter)` → "Showing X tasks" message
- `render_import_result(result: ImportResult)` → import operation summary
- Date/time formatting helpers
- Table/column formatting utilities (future: JSON/CSV output formats)

**Size**: ~100-150 lines
**Dependencies**: tasky_tasks models (TaskStatus, Task)

**Example**:
```python
def get_status_indicator(status: TaskStatus) -> str:
    """Return visual indicator for task status."""
    return {
        TaskStatus.PENDING: "○",
        TaskStatus.COMPLETED: "●",
        TaskStatus.CANCELLED: "✗",
    }[status]

def render_task_list(
    tasks: list[Task],
    *,
    show_id: bool = False,
    show_status: bool = False,
) -> None:
    """Render task list to stdout."""
    for task in tasks:
        parts = []
        if show_status:
            parts.append(get_status_indicator(task.status))
        if show_id:
            parts.append(f"[{task.task_id}]")
        parts.append(task.name)
        typer.echo(" ".join(parts))
```

---

### `tasks/validation.py` (Input Validation)
**Responsibility**: Input parsing, validation, type conversion

**Contents**:
- `parse_task_id(task_id_str: str) -> UUID` (raises typer.Exit on invalid UUID)
- `parse_date_option(date_str: str, inclusive_end: bool) -> datetime` (consolidated date parsing)
- `is_valid_date_format(date_str: str) -> bool`
- `validate_status_option(status_str: str) -> list[TaskStatus] | None`
- `parse_task_id_and_get_service(task_id: str) -> tuple[TaskService, UUID]`
- `validate_name_not_empty(name: str) -> None`
- `validate_import_strategy(strategy: str) -> None`
- Context helpers: `is_verbose(ctx)`, `convert_context(ctx)`

**Size**: ~150 lines
**Dependencies**: typer, tasky_tasks models

**Example**:
```python
def parse_date_option(date_str: str, *, inclusive_end: bool = False) -> datetime:
    """Parse and validate date string, returning timezone-aware datetime.

    Args:
        date_str: ISO 8601 date string (YYYY-MM-DD or full datetime)
        inclusive_end: If True, set time to 23:59:59 (for created_before queries)

    Returns:
        Timezone-aware datetime

    Raises:
        typer.Exit: If date format is invalid
    """
    if not is_valid_date_format(date_str):
        typer.echo(
            f"Invalid date format: '{date_str}'. "
            "Expected ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
            err=True,
        )
        raise typer.Exit(1)

    try:
        parsed_date = datetime.fromisoformat(date_str)
        if inclusive_end and parsed_date.hour == 0:
            # User specified date-only; make it inclusive end-of-day
            parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
        return parsed_date.astimezone(UTC) if parsed_date.tzinfo else parsed_date.replace(tzinfo=UTC)
    except ValueError as exc:
        typer.echo(f"Invalid date: {exc}", err=True)
        raise typer.Exit(1) from None
```

---

## Migration Strategy

### Phase 1: Create Module Structure (Non-breaking)
1. Create `tasks/` directory
2. Create `__init__.py` with imports from original `tasks.py`
3. Update `tasky_cli/commands/__init__.py` to import from `tasks` module instead of `tasks.py`
4. Run all tests → verify zero failures

### Phase 2: Extract Validation Module
1. Move validation helpers to `validation.py`
2. Update imports in `tasks.py` (now `commands.py`)
3. Run all tests → verify behavioral equivalence

### Phase 3: Extract Formatting Module
1. Move formatting helpers to `formatting.py`
2. Update imports
3. Run all tests → verify equivalence

### Phase 4: Extract Error Handling Module
1. Move error handlers to `error_handling.py`
2. Move decorator
3. Update imports
4. Run all tests → verify equivalence

### Phase 5: Finalize Commands Module
1. Rename `tasks.py` → `commands.py` (if not already done)
2. Move to `tasks/` directory
3. Clean up imports
4. Run all tests → final verification

### Phase 6: Add Module-Level Tests
1. Add unit tests for `validation.py` (test date parsing edge cases)
2. Add unit tests for `formatting.py` (test status indicators, output rendering)
3. Add unit tests for `error_handling.py` (test error routing logic)

## Testing Strategy

### Behavioral Equivalence Tests
- All existing 577 tests must pass after each phase
- No changes to test files required (tests import from `tasks` module, internal structure is transparent)

### New Module-Level Tests
- `test_validation.py`: Test input parsing edge cases
  - Invalid UUIDs
  - Invalid date formats
  - Boundary dates (timezone handling)
  - Empty/None inputs

- `test_formatting.py`: Test output rendering
  - Status indicators for all states
  - Task list with various combinations of flags
  - Summary message formatting

- `test_error_handling.py`: Test error routing
  - Each exception type routes to correct handler
  - Verbose mode shows stack trace
  - Non-verbose mode shows user-friendly message
  - Exit codes are correct

## Rollback Plan

If issues arise:
1. Revert PR
2. Original `tasks.py` still exists in git history
3. Zero external API changes means zero downstream breakage

## Success Criteria

✅ All existing tests pass (577 tests, 100%)
✅ Ruff/pyright checks pass with zero new errors
✅ No complexity warnings in any new module (`noqa: C901` removed)
✅ Each module <250 lines
✅ Clear module boundaries (no circular imports)
✅ Documentation updated (module docstrings, architecture notes)
