# Spec Delta: task-cli-operations

## ADDED Requirements

### Requirement: Task CLI Module Structure

The task CLI commands SHALL be organized into a modular structure with clear separation of concerns to support maintainability and future growth.

#### Module Organization

The task commands SHALL be structured as follows:

```
tasky_cli/commands/tasks/
  __init__.py              # Public API: exports task_app
  commands.py              # Command definitions and orchestration
  error_handling.py        # Exception handlers and error rendering
  formatting.py            # Output formatting and display logic
  validation.py            # Input validation and parsing
```

**Each module SHALL have a single responsibility:**

- `__init__.py`: Export public interface (`task_app`) for app registration
- `commands.py`: Typer command definitions, orchestration between validation/service/formatting
- `error_handling.py`: Exception handling, error routing, error message rendering, verbose mode support
- `formatting.py`: Task list rendering, detail views, status indicators, summary messages
- `validation.py`: Input parsing (UUIDs, dates, status), validation, type conversion

**Constraints:**
- No module SHALL exceed 400 lines
- No function SHALL have cyclomatic complexity >10 (no `noqa: C901` suppressions)
- Modules SHALL NOT have circular dependencies
- All modules SHALL have comprehensive docstrings

#### Scenario: Command imports from modular structure

```gherkin
Given the task CLI module is split into focused modules
When the tasky CLI app imports task commands via "from tasky_cli.commands.tasks import task_app"
Then the task_app is available for registration
And all task commands (create, list, show, update, etc.) are registered
And the public API is unchanged from the previous monolithic structure
```

#### Scenario: Behavioral equivalence after refactoring

```gherkin
Given the task CLI module has been refactored into modular structure
When any task command is executed (create, list, show, update, complete, cancel, reopen, delete, import, export)
Then the command behavior is identical to the previous monolithic implementation
And the output format is unchanged
And error messages are unchanged
And exit codes are unchanged
And all existing tests pass without modification
```

---

### Requirement: Input Validation Module

The task CLI SHALL provide a dedicated validation module for parsing and validating user inputs with consistent error handling.

#### Validation Functions

The `validation.py` module SHALL provide:

- `parse_task_id(task_id_str: str) -> UUID`: Parse and validate task ID, exit with helpful error if invalid
- `parse_date_option(date_str: str, *, inclusive_end: bool) -> datetime`: Parse ISO 8601 date with timezone handling
- `is_valid_date_format(date_str: str) -> bool`: Validate date format before parsing
- `validate_status_option(status_str: str) -> list[TaskStatus] | None`: Parse status filter option
- `parse_task_id_and_get_service(task_id: str) -> tuple[TaskService, UUID]`: Combined task ID parsing + service retrieval
- `validate_name_not_empty(name: str) -> None`: Ensure task name is non-empty
- `validate_import_strategy(strategy: str) -> None`: Validate import strategy is recognized

**Error Handling:**
- All validation functions SHALL raise `typer.Exit(1)` with user-friendly error message on invalid input
- Error messages SHALL include what was invalid and what format is expected
- No raw exceptions SHALL leak to user (all wrapped in `typer.Exit`)

#### Scenario: Date validation with consistent error handling

```gherkin
Given a user runs "tasky task list --created-after invalid-date"
When the validation module parses the date option
Then parse_date_option raises typer.Exit(1)
And the error message includes "Invalid date format: 'invalid-date'"
And the error message includes "Expected ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
And the CLI exits with code 1
```

#### Scenario: UUID validation with helpful feedback

```gherkin
Given a user runs "tasky task show not-a-uuid"
When the validation module parses the task ID
Then parse_task_id raises typer.Exit(1)
And the error message includes "Invalid task ID format"
And the error message includes the invalid value "not-a-uuid"
And the error message suggests "Expected UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
And the CLI exits with code 1
```

#### Scenario: Date parsing with timezone awareness

```gherkin
Given a user runs "tasky task list --created-after 2025-11-15"
When the validation module parses the date option with inclusive_end=False
Then parse_date_option returns a timezone-aware datetime
And the datetime is in UTC timezone
And the time component is 00:00:00 (start of day)
```

```gherkin
Given a user runs "tasky task list --created-before 2025-11-15"
When the validation module parses the date option with inclusive_end=True
Then parse_date_option returns a timezone-aware datetime
And the time component is 23:59:59 (end of day)
And the datetime is in UTC timezone
```

---

### Requirement: Output Formatting Module

The task CLI SHALL provide a dedicated formatting module for consistent output rendering across all commands.

#### Formatting Functions

The `formatting.py` module SHALL provide:

- `get_status_indicator(status: TaskStatus) -> str`: Return visual indicator for task status (○ pending, ● completed, ✗ cancelled)
- `render_task_list(tasks, *, show_id, show_status, ...) -> None`: Render task list to stdout
- `render_task_detail(task: Task) -> None`: Render single task detail view
- `render_list_summary(tasks, filter) -> None`: Render "Showing X tasks" summary message
- `render_import_result(result: ImportResult) -> None`: Render import operation summary

**Output Principles:**
- All rendering functions write to stdout (or stderr for errors)
- Formatting SHALL be consistent with existing output format (behavioral equivalence)
- Future: Support for JSON/CSV output formats can be added to this module

#### Scenario: Task list rendering with status indicators

```gherkin
Given a project with 3 tasks: 1 pending, 1 completed, 1 cancelled
When the formatting module renders the task list with show_status=True
Then each task line includes a status indicator
And pending tasks show "○"
And completed tasks show "●"
And cancelled tasks show "✗"
And the output format matches the existing monolithic implementation
```

#### Scenario: List summary message formatting

```gherkin
Given a task list with 5 total tasks
And a filter that matches 3 tasks
When the formatting module renders the list summary
Then the summary message shows "Showing 3 of 5 tasks"
And the message is written to stdout
```

---

### Requirement: Error Handling Module

The task CLI SHALL provide a dedicated error handling module for consistent exception handling and error rendering across all commands.

#### Error Handling Components

The `error_handling.py` module SHALL provide:

- `Handler` protocol: Type definition for exception handler functions
- `with_task_error_handling` decorator: Wraps commands to catch and handle exceptions
- `render_error(message, suggestion, *, verbose, exc)`: Render error message with optional suggestion and stack trace
- `dispatch_exception(exc, *, verbose)`: Route exception to appropriate handler
- `route_exception_to_handler(exc, *, verbose)`: Determine which handler to use for exception type
- Handler functions for each exception type:
  - `handle_task_domain_error`
  - `handle_task_not_found`
  - `handle_task_validation_error`
  - `handle_invalid_transition`
  - `handle_import_format_error`
  - `handle_import_export_error`
  - `handle_storage_error`
  - `handle_project_not_found_error`
  - `handle_backend_not_registered_error`
- `suggest_transition(status)`: State machine transition suggestions

**Error Handling Principles:**
- All handlers SHALL call `render_error()` for consistent error output
- Verbose mode SHALL show full stack trace
- Non-verbose mode SHALL show user-friendly message + suggestion
- Exit codes SHALL be consistent: 1 for user errors, 3 for storage errors

#### Scenario: Error routing to appropriate handler

```gherkin
Given a command wrapped with @with_task_error_handling
When the command raises TaskNotFoundError
Then dispatch_exception routes to handle_task_not_found
And the error is rendered with appropriate message
And the CLI exits with code 1
```

#### Scenario: Verbose error output

```gherkin
Given a command fails with a StorageError
And the user runs the command with --verbose flag
When the error handler renders the error
Then the output includes the user-friendly error message
And the output includes "Detailed error:" section
And the output includes the full stack trace
And the CLI exits with code 3
```

#### Scenario: State transition suggestions

```gherkin
Given a user tries to complete an already completed task
When the error handler handles InvalidStateTransitionError
Then the error message includes "Task is already completed"
And the suggestion includes possible transitions (e.g., "cancel" or "reopen")
And the CLI exits with code 1
```

---

## MODIFIED Requirements

None. This change is purely internal refactoring with no modifications to existing requirements.

---

## REMOVED Requirements

None. All existing requirements are preserved.
