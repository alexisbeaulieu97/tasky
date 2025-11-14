"""Commands related to task management in Tasky CLI."""

from __future__ import annotations

import re
import sys
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import NoReturn, Protocol, TypeVar, cast
from uuid import UUID

import click
import typer
from pydantic import ValidationError as PydanticValidationError
from tasky_settings import ProjectNotFoundError, create_task_service
from tasky_storage.errors import StorageError
from tasky_tasks import (
    ExportError,
    ImportResult,
    IncompatibleVersionError,
    InvalidExportFormatError,
    InvalidStateTransitionError,
    TaskDomainError,
    TaskFilter,
    TaskImportError,
    TaskImportExportService,
    TaskNotFoundError,
    TaskValidationError,
)
from tasky_tasks.models import TaskStatus
from tasky_tasks.service import TaskService

task_app = typer.Typer(no_args_is_help=True)

F = TypeVar("F", bound=Callable[..., object])


class Handler(Protocol):
    """Protocol for exception handler functions."""

    def __call__(self, exc: Exception, *, verbose: bool) -> NoReturn:
        """Handle an exception with optional verbose output."""
        ...


_VERBOSE_KEY = "verbose"


@task_app.callback()
def task_app_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--verbose",
        "-v",
        help="Show detailed error information, including stack traces.",
    ),
) -> None:
    """Configure task command context."""
    ctx.ensure_object(dict)
    ctx.obj[_VERBOSE_KEY] = verbose


def with_task_error_handling(func: F) -> F:  # noqa: UP047
    """Apply consistent error handling for task commands."""

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        ctx = click.get_current_context(silent=True)
        # Convert Click context to a generic dict-like object for _is_verbose
        typer_ctx = _convert_context(ctx)
        verbose = _is_verbose(typer_ctx)

        try:
            return func(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch-all  # noqa: BLE001
            _dispatch_exception(exc, verbose=verbose)

    return cast("F", wrapper)


def _parse_task_id_and_get_service(task_id: str) -> tuple[TaskService, UUID]:
    """Parse task ID and initialize task service.

    This helper handles common setup for task commands:
    - UUID parsing with error handling (before service creation)
    - Project validation (via error dispatcher)
    - Task service initialization

    Args:
        task_id: The task ID string from CLI input.

    Returns:
        Tuple of (TaskService instance, parsed UUID).

    Raises:
        typer.Exit: On invalid UUID format
        ProjectNotFoundError: If no project found (caught by error dispatcher)
        KeyError: If backend not registered (caught by error dispatcher)

    """
    # Parse UUID first, before creating service or checking for project
    # This ensures invalid UUIDs are rejected without touching storage
    try:
        uuid = UUID(task_id)
    except ValueError as exc:
        typer.echo(
            f"Invalid UUID format: {task_id}\n"
            f"Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "
            f"(e.g., 123e4567-e89b-12d3-a456-426614174000)",
            err=True,
        )
        raise typer.Exit(1) from exc

    # Only create service after UUID is validated
    service = _get_service()

    return service, uuid


@task_app.command(name="list")
@with_task_error_handling
def list_command(  # noqa: C901, PLR0912, PLR0915
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter tasks by status (pending, completed, cancelled).",
    ),
    created_after: str | None = typer.Option(
        None,
        "--created-after",
        help="Filter tasks created on or after this date (ISO 8601: YYYY-MM-DD).",
    ),
    created_before: str | None = typer.Option(
        None,
        "--created-before",
        help="Filter tasks created before this date (ISO 8601: YYYY-MM-DD).",
    ),
    search: str | None = typer.Option(
        None,
        "--search",
        help="Search tasks by name or details (case-insensitive).",
    ),
    long: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--long",
        "-l",
        help="Show timestamps (created_at and updated_at) for each task.",
    ),
) -> None:
    """List all tasks with status indicators and IDs.

    Output format:
        {status} {id} {name} - {details}

    Status indicators:
        ○ = pending
        ✓ = completed
        ✗ = cancelled

    Tasks are sorted by status: pending first, then completed, then cancelled.

    Filtering:
        --status:         Filter by task status (pending, completed, cancelled)
        --created-after:  Show tasks created on or after a date (YYYY-MM-DD)
        --created-before: Show tasks created before a date (YYYY-MM-DD)
        --search:         Search task name and details (case-insensitive)

    Multiple filters are combined with AND logic (all must match).

    Example:
        $ tasky task list
        ○ 550e8400-e29b-41d4-a716-446655440000 Buy groceries - Get milk and eggs
        ✓ 550e8400-e29b-41d4-a716-446655440001 Review PR - Check code quality

        Showing 2 tasks (1 pending, 1 completed, 0 cancelled)

        $ tasky task list --status pending --created-after 2025-11-01
        ○ 550e8400-e29b-41d4-a716-446655440000 Buy groceries - Get milk and eggs

        Showing 1 task (1 pending, 0 completed, 0 cancelled)

        $ tasky task list --search "groceries"
        ○ 550e8400-e29b-41d4-a716-446655440000 Buy groceries - Get milk and eggs

        Showing 1 task (1 pending, 0 completed, 0 cancelled)

    """
    # Validate status argument first, before creating service
    # This ensures invalid status values are rejected without requiring a project
    task_status: TaskStatus | None = None

    if status is not None:
        valid_statuses = {s.value for s in TaskStatus}
        if status.lower() not in valid_statuses:
            valid_list = ", ".join(sorted(valid_statuses))
            typer.echo(
                f"Invalid status: '{status}'. Valid options: {valid_list}",
                err=True,
            )
            raise typer.Exit(1)
        task_status = TaskStatus(status.lower())

    # Parse and validate date arguments
    created_after_dt: datetime | None = None
    created_before_dt: datetime | None = None

    if created_after is not None:
        # Validate format is exactly YYYY-MM-DD (reject time components)
        if not _is_valid_date_format(created_after):
            typer.echo(
                f"Invalid date format: '{created_after}'. "
                "Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)",
                err=True,
            )
            raise typer.Exit(1) from None
        try:
            # Parse date and make it timezone-aware (UTC midnight)
            parsed_date = datetime.fromisoformat(created_after)
            created_after_dt = parsed_date.replace(tzinfo=UTC)
        except ValueError:
            typer.echo(
                f"Invalid date format: '{created_after}'. "
                "Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)",
                err=True,
            )
            raise typer.Exit(1) from None

    if created_before is not None:
        # Validate format is exactly YYYY-MM-DD (reject time components)
        if not _is_valid_date_format(created_before):
            typer.echo(
                f"Invalid date format: '{created_before}'. "
                "Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)",
                err=True,
            )
            raise typer.Exit(1) from None
        try:
            parsed_date = datetime.fromisoformat(created_before)
            # Add 1 day to make the exclusive < check inclusive of the entire day
            # (user expects --created-before 2025-12-31 to include all of Dec 31)
            created_before_dt = parsed_date.replace(tzinfo=UTC) + timedelta(days=1)
        except ValueError:
            typer.echo(
                f"Invalid date format: '{created_before}'. "
                "Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)",
                err=True,
            )
            raise typer.Exit(1) from None

    # Only create service after validating input
    service = _get_service()

    # Normalize empty search to None (per spec: empty search = no filter)
    if search is not None and not search.strip():
        search = None

    # Build filter and fetch tasks
    has_filters = (
        task_status is not None
        or created_after_dt is not None
        or created_before_dt is not None
        or search is not None
    )

    if has_filters:
        # Build TaskFilter with specified criteria
        task_filter = TaskFilter(
            statuses=[task_status] if task_status is not None else None,
            created_after=created_after_dt,
            created_before=created_before_dt,
            name_contains=search,
        )
        tasks = service.find_tasks(task_filter)
    else:
        tasks = service.get_all_tasks()

    if not tasks:
        # Show filter-specific message when filtering, generic message otherwise
        if has_filters:
            typer.echo("No matching tasks found")
        else:
            typer.echo("No tasks to display")
        return

    # Sort tasks by status: pending → completed → cancelled
    status_order = {TaskStatus.PENDING: 0, TaskStatus.COMPLETED: 1, TaskStatus.CANCELLED: 2}
    sorted_tasks = sorted(tasks, key=lambda t: status_order[t.status])

    # Count tasks by status
    pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    completed_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    cancelled_count = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)

    # Display tasks with status indicators
    for task in sorted_tasks:
        # Map status to indicator
        status_indicator = _get_status_indicator(task.status)
        typer.echo(f"{status_indicator} {task.task_id} {task.name} - {task.details}")

        # Show timestamps if --long flag is provided
        if long:
            created = task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            updated = task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            typer.echo(f"  Created: {created} | Modified: {updated}")

    # Display summary line
    task_word = "task" if len(tasks) == 1 else "tasks"
    typer.echo(
        f"\nShowing {len(tasks)} {task_word} "
        f"({pending_count} pending, {completed_count} completed, "
        f"{cancelled_count} cancelled)",
    )


def _is_valid_date_format(date_str: str) -> bool:
    """Validate that date string matches exactly YYYY-MM-DD format.

    Args:
        date_str: The date string to validate.

    Returns:
        True if format is YYYY-MM-DD, False otherwise.

    """
    # Reject any string containing time markers (T, colon, etc.)
    if "T" in date_str or ":" in date_str or "+" in date_str or "Z" in date_str:
        return False
    # Must match YYYY-MM-DD exactly
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))


def _get_status_indicator(status: TaskStatus) -> str:
    """Get the visual indicator for a task status.

    Args:
        status: The task status.

    Returns:
        A single-character indicator (○, ✓, or ✗).

    """
    indicators = {
        TaskStatus.PENDING: "○",
        TaskStatus.COMPLETED: "✓",
        TaskStatus.CANCELLED: "✗",
    }
    return indicators[status]


def _validate_and_apply_update_fields(
    task: object,
    name: str | None,
    details: str | None,
) -> None:
    """Validate and apply update fields to a task object.

    Args:
        task: The task object to update (must have name and details attributes).
        name: New task name (optional).
        details: New task details (optional).

    Raises:
        typer.Exit: If validation fails (empty fields).

    """
    if name is not None:
        name = name.strip()
        if not name:
            typer.echo("name cannot be empty", err=True)
            raise typer.Exit(1)
        task.name = name  # type: ignore[attr-defined]
    if details is not None:
        details = details.strip()
        if not details:
            typer.echo("details cannot be empty", err=True)
            raise typer.Exit(1)
        task.details = details  # type: ignore[attr-defined]


@task_app.command(name="show")
@with_task_error_handling
def show_command(task_id: str = typer.Argument(..., help="Task ID (UUID format)")) -> None:
    """Display full details for a specific task.

    Shows all task metadata including ID, name, details, status, and timestamps.

    Args:
        task_id: The UUID of the task to display.

    Example:
        $ tasky task show 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60

        Task Details
        ID: 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60
        Name: Buy groceries
        Details: Get milk and eggs from the store
        Status: PENDING
        Created: 2025-11-12 14:30:45
        Updated: 2025-11-12 14:30:45

    """
    service, uuid = _parse_task_id_and_get_service(task_id)
    task = service.get_task(uuid)

    # Display task details in human-readable format
    typer.echo("Task Details")
    typer.echo(f"ID: {task.task_id}")
    typer.echo(f"Name: {task.name}")
    typer.echo(f"Details: {task.details}")
    typer.echo(f"Status: {task.status.value.upper()}")
    typer.echo(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    typer.echo(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


@task_app.command(name="create")
@with_task_error_handling
def create_command(
    name: str = typer.Argument(..., help="Task name"),
    details: str = typer.Argument(..., help="Task details/description"),
) -> None:
    """Create a new task.

    Examples:
        tasky task create "Buy groceries" "Get milk and eggs from the store"
        tasky task create "Review PR" "Check code quality and tests"

    """
    service = _get_service()
    task = service.create_task(name, details)

    # Display success message and task details
    typer.echo("Task created successfully!")
    typer.echo(f"ID: {task.task_id}")
    typer.echo(f"Name: {task.name}")
    typer.echo(f"Details: {task.details}")
    typer.echo(f"Status: {task.status.value.upper()}")
    typer.echo(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


@task_app.command(name="update")
@with_task_error_handling
def update_command(
    task_id: str = typer.Argument(..., help="Task ID (UUID format)"),
    name: str | None = typer.Option(None, "--name", help="New task name"),
    details: str | None = typer.Option(None, "--details", help="New task details"),
) -> None:
    r"""Update an existing task's name and/or details.

    At least one of --name or --details must be provided.
    Only the specified fields will be updated; unspecified fields remain unchanged.

    Args:
        task_id: The UUID of the task to update.
        name: New task name (optional).
        details: New task details (optional).

    Examples:
        tasky task update <task-id> --name "New name" --details "New details"
        tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60 --name "Updated name"
        tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60 --details "Updated details"

    """
    # Validate that at least one field is provided
    if name is None and details is None:
        typer.echo(
            "Error: At least one of --name or --details must be provided.",
            err=True,
        )
        typer.echo(
            'Example: tasky task update <task-id> --name "New name"',
            err=True,
        )
        raise typer.Exit(1)

    # Parse task ID and get service
    service, uuid = _parse_task_id_and_get_service(task_id)

    # Retrieve the current task
    task = service.get_task(uuid)

    # Validate and apply updates to task
    _validate_and_apply_update_fields(task, name, details)

    # Persist changes
    service.update_task(task)

    # Display updated task details
    typer.echo("Task updated successfully!")
    typer.echo(f"ID: {task.task_id}")
    typer.echo(f"Name: {task.name}")
    typer.echo(f"Details: {task.details}")
    typer.echo(f"Status: {task.status.value.upper()}")
    typer.echo(f"Modified: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


def _get_service() -> TaskService:
    """Get or create a task service for the current project.

    Returns:
        Configured TaskService instance

    Raises:
        ProjectNotFoundError: If no project found
        KeyError: If configured backend is not registered

    """
    return create_task_service()


def _convert_context(ctx: click.Context | None) -> typer.Context | None:
    """Convert a Click context to a Typer context."""
    if ctx is None:
        return None
    # Typer.Context is a subclass of click.Context, so we can cast safely
    return ctx  # type: ignore[return-value]


def _is_verbose(ctx: typer.Context | None) -> bool:
    current = ctx
    while current is not None:
        obj: object = current.obj
        if isinstance(obj, dict):
            value: bool = bool(obj.get(_VERBOSE_KEY, False))
            return value
        current = current.parent
    return False


def _suggest_transition(
    from_status: TaskStatus | str,
    to_status: TaskStatus | str,
    task_id: str,
) -> str:
    """Generate context-aware suggestions for invalid state transitions.

    Args:
        from_status: The current status that prevents the transition.
        to_status: The desired target status.
        task_id: The task ID to include in the suggestion.

    Returns:
        A helpful suggestion string for the user.

    """
    # Normalize to TaskStatus enums for consistent comparison
    from_enum = from_status if isinstance(from_status, TaskStatus) else TaskStatus(from_status)
    to_enum = to_status if isinstance(to_status, TaskStatus) else TaskStatus(to_status)

    # Map of (from_status, to_status) -> suggestion
    reopen_suggestion = f"Use 'tasky task reopen {task_id}' to make it pending first."
    completed_suggestion = (
        f"Task is already completed. Use 'tasky task reopen {task_id}' if you want to make changes."
    )
    cancelled_suggestion = (
        f"Task is already cancelled. Use 'tasky task reopen {task_id}' if you want to make changes."
    )
    suggestions = {
        (TaskStatus.CANCELLED, TaskStatus.COMPLETED): reopen_suggestion,
        (TaskStatus.COMPLETED, TaskStatus.CANCELLED): reopen_suggestion,
        (TaskStatus.COMPLETED, TaskStatus.COMPLETED): completed_suggestion,
        (TaskStatus.CANCELLED, TaskStatus.CANCELLED): cancelled_suggestion,
        (TaskStatus.PENDING, TaskStatus.PENDING): "Task is already pending. No action needed.",
    }

    # Return specific suggestion or generic fallback
    return suggestions.get(
        (from_enum, to_enum),
        f"Use 'tasky task list' to inspect the current status of task '{task_id}'.",
    )


def _render_error(
    message: str,
    *,
    suggestion: str | None = None,
    verbose: bool,
    exc: Exception | None = None,
) -> None:
    typer.echo(f"Error: {message}", err=True)
    if suggestion:
        typer.echo(f"Suggestion: {suggestion}", err=True)
    if verbose and exc is not None:
        typer.echo("", err=True)
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)


def _dispatch_exception(exc: Exception, *, verbose: bool) -> NoReturn:
    if isinstance(exc, typer.Exit):
        raise exc

    # Dispatch to appropriate handler
    _route_exception_to_handler(exc, verbose=verbose)


def _route_exception_to_handler(exc: Exception, *, verbose: bool) -> NoReturn:
    """Route exception to the appropriate error handler."""
    handler_chain: tuple[tuple[type[Exception], Handler], ...] = (
        (TaskDomainError, cast("Handler", _handle_task_domain_error)),
        (StorageError, cast("Handler", _handle_storage_error)),
        (KeyError, cast("Handler", _handle_backend_not_registered_error)),
        (ProjectNotFoundError, cast("Handler", _handle_project_not_found_error)),
        (PydanticValidationError, cast("Handler", _handle_pydantic_validation_error)),
    )

    for exc_type, handler in handler_chain:
        if isinstance(exc, exc_type):
            handler(exc, verbose=verbose)

    # Fallback for unexpected errors
    _handle_unexpected_error(exc, verbose=verbose)


def _handle_task_domain_error(exc: TaskDomainError, *, verbose: bool) -> NoReturn:
    # Route to specific handlers
    _route_task_domain_error(exc, verbose=verbose)
    raise typer.Exit(1) from exc


def _route_task_domain_error(exc: TaskDomainError, *, verbose: bool) -> None:
    """Route task domain error to appropriate handler."""
    if isinstance(exc, TaskNotFoundError):
        _handle_task_not_found(exc, verbose=verbose)
        return

    if isinstance(exc, TaskValidationError):
        _handle_task_validation_error(exc, verbose=verbose)
        return

    if isinstance(exc, InvalidStateTransitionError):
        _handle_invalid_transition(exc, verbose=verbose)
        return

    if _try_handle_import_export_errors(exc, verbose=verbose):
        return

    _render_error(str(exc) or "Task operation failed.", verbose=verbose, exc=exc)


def _try_handle_import_export_errors(exc: TaskDomainError, *, verbose: bool) -> bool:
    """Try to handle import/export errors. Returns True if handled."""
    # Handle all import/export errors together
    import_export_types = (
        InvalidExportFormatError,
        IncompatibleVersionError,
        ExportError,
        TaskImportError,
    )
    if not isinstance(exc, import_export_types):
        return False

    if isinstance(exc, (InvalidExportFormatError, IncompatibleVersionError)):
        _handle_import_format_error(exc, verbose=verbose)
    else:
        _handle_import_export_error(exc, verbose=verbose)
    return True


def _handle_task_not_found(exc: TaskNotFoundError, *, verbose: bool) -> None:
    """Handle TaskNotFoundError."""
    _render_error(
        f"Task '{exc.task_id}' not found.",
        suggestion="Run 'tasky task list' to view available tasks.",
        verbose=verbose,
        exc=exc,
    )


def _handle_task_validation_error(exc: TaskValidationError, *, verbose: bool) -> None:
    """Handle TaskValidationError."""
    suggestion = None
    if getattr(exc, "field", None):
        suggestion = f"Check the value provided for '{exc.field}'."
    message = str(exc) or "Task validation failed."
    _render_error(message, suggestion=suggestion, verbose=verbose, exc=exc)


def _handle_invalid_transition(exc: InvalidStateTransitionError, *, verbose: bool) -> None:
    """Handle InvalidStateTransitionError."""
    # Extract user-facing labels from status values (handle both enum and string)
    from_label = getattr(exc.from_status, "value", str(exc.from_status))
    to_label = getattr(exc.to_status, "value", str(exc.to_status))

    suggestion = _suggest_transition(
        from_status=exc.from_status,
        to_status=exc.to_status,
        task_id=str(exc.task_id),
    )
    _render_error(
        f"Cannot transition from {from_label} to {to_label}.",
        suggestion=suggestion,
        verbose=verbose,
        exc=exc,
    )


def _handle_import_format_error(exc: TaskDomainError, *, verbose: bool) -> None:
    """Handle InvalidExportFormatError and IncompatibleVersionError."""
    if isinstance(exc, InvalidExportFormatError):
        _render_error(
            f"Invalid file format: {exc}",
            suggestion="Ensure the file is a valid JSON export from tasky.",
            verbose=verbose,
            exc=exc,
        )
    elif isinstance(exc, IncompatibleVersionError):
        version_info = f" (found: {exc.actual})" if exc.actual else ""
        _render_error(
            f"Incompatible format version{version_info}",
            suggestion="The export file may be from a different version of tasky.",
            verbose=verbose,
            exc=exc,
        )


def _handle_import_export_error(exc: TaskDomainError, *, verbose: bool) -> None:
    """Handle ExportError and TaskImportError."""
    if isinstance(exc, ExportError):
        _render_error(
            f"Export failed: {exc}",
            suggestion="Check file permissions and disk space.",
            verbose=verbose,
            exc=exc,
        )
    elif isinstance(exc, TaskImportError):
        _render_error(
            f"Import failed: {exc}",
            suggestion="Verify the import file exists and is readable.",
            verbose=verbose,
            exc=exc,
        )


def _handle_storage_error(exc: StorageError, *, verbose: bool) -> NoReturn:
    _render_error(
        "Storage failure encountered. Verify project initialization and file permissions.",
        suggestion="Run 'tasky project init' or check the .tasky directory.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(3) from exc


def _handle_project_not_found_error(exc: ProjectNotFoundError, *, verbose: bool) -> NoReturn:
    _render_error(
        "No project found in current directory.",
        suggestion="Run 'tasky project init' to create a project.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from exc


def _handle_backend_not_registered_error(exc: KeyError, *, verbose: bool) -> NoReturn:
    """Render backend registry errors with actionable guidance."""
    details = exc.args[0] if exc.args else "Configured backend is not registered."
    _render_error(
        str(details),
        suggestion="Update .tasky/config.toml or re-run 'tasky project init' with a valid backend.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from exc


def _handle_pydantic_validation_error(exc: PydanticValidationError, *, verbose: bool) -> NoReturn:
    """Handle Pydantic validation errors with user-friendly messages."""
    # Extract the first error for a clean message
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = first_error.get("loc", ("unknown",))[-1]
        message = first_error.get("msg", "Validation failed")
        _render_error(
            f"{message.capitalize()} for field '{field}'.",
            suggestion="Check your input values and try again.",
            verbose=verbose,
            exc=exc,
        )
    else:
        _render_error(
            "Validation failed.",
            suggestion="Check your input values and try again.",
            verbose=verbose,
            exc=exc,
        )
    raise typer.Exit(1) from exc


def _handle_unexpected_error(exc: Exception, *, verbose: bool) -> NoReturn:
    _render_error(
        "An unexpected error occurred.",
        suggestion="Run with --verbose for details or file a bug report.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from exc


@task_app.command(name="complete")
@with_task_error_handling
def complete_command(task_id: str) -> None:
    """Mark a task as completed.

    Args:
        task_id: The UUID of the task to complete.

    """
    service, uuid = _parse_task_id_and_get_service(task_id)
    task = service.complete_task(uuid)
    typer.echo(f"✓ Task completed: {task.name}")
    typer.echo(f"  Completed at: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


@task_app.command(name="cancel")
@with_task_error_handling
def cancel_command(task_id: str) -> None:
    """Mark a task as cancelled.

    Args:
        task_id: The UUID of the task to cancel.

    """
    service, uuid = _parse_task_id_and_get_service(task_id)
    task = service.cancel_task(uuid)
    typer.echo(f"✗ Task cancelled: {task.name}")


@task_app.command(name="reopen")
@with_task_error_handling
def reopen_command(task_id: str) -> None:
    """Reopen a completed or cancelled task.

    Args:
        task_id: The UUID of the task to reopen.

    """
    service, uuid = _parse_task_id_and_get_service(task_id)
    task = service.reopen_task(uuid)
    typer.echo(f"↻ Task reopened: {task.name}")


@task_app.command(name="export")
@with_task_error_handling
def export_command(
    file_path: str = typer.Argument(..., help="Path to export JSON file"),
) -> None:
    """Export tasks to a JSON file.

    Exports all tasks to a JSON backup file. The file can be imported later
    using the 'task import' command.

    Examples:
        tasky task export backup.json

    """
    service = _get_service()
    export_service = TaskImportExportService(service)

    export_path = Path(file_path)
    export_doc = export_service.export_tasks(export_path)

    typer.echo(f"✓ Exported {export_doc.task_count} tasks to: {file_path}")


@task_app.command(name="import")
@with_task_error_handling
def import_command(
    file_path: str = typer.Argument(..., help="Path to import JSON file"),
    strategy: str = typer.Option(
        "append",
        "--strategy",
        "-S",
        help="Import strategy: append (add new), replace (clear all first), merge (update by ID)",
    ),
    dry_run: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--dry-run",
        "-n",
        help="Show what would be imported without making changes",
    ),
) -> None:
    """Import tasks from a JSON file.

    Imports tasks from a JSON backup file with different merge strategies:

    - append: Adds imported tasks (default), re-keys duplicates with new IDs
    - replace: Clears all existing tasks first, then imports
    - merge: Updates existing tasks by ID, creates new ones

    Examples:
        tasky task import backup.json
        tasky task import backup.json --strategy merge
        tasky task import backup.json --dry-run

    """
    # Validate and normalize strategy (case-insensitive)
    strategy = _validate_import_strategy(strategy)

    service = _get_service()
    export_service = TaskImportExportService(service)

    import_path = Path(file_path)
    result = export_service.import_tasks(import_path, strategy=strategy, dry_run=dry_run)

    # Show results
    _display_import_results(result, dry_run=dry_run)


def _validate_import_strategy(strategy: str) -> str:
    """Validate import strategy (case-insensitive) and return normalized value."""
    valid_strategies = ["append", "replace", "merge"]
    normalized = strategy.lower()
    if normalized not in valid_strategies:
        typer.echo(f"✗ Invalid strategy: {strategy}", err=True)
        typer.echo(f"  Valid strategies: {', '.join(valid_strategies)}", err=True)
        raise typer.Exit(1)
    return normalized


def _display_import_results(result: ImportResult, *, dry_run: bool) -> None:
    """Display import results with statistics."""
    max_errors_shown = 5

    # Format output per spec requirements
    if dry_run:
        typer.echo(f"[DRY RUN] Would import: {result.created} created, {result.updated} updated")
    else:
        typer.echo(f"✓ Import complete: {result.created} created, {result.updated} updated")

    # Show skipped count if there were errors
    if result.skipped > 0:
        typer.echo(f"  Skipped: {result.skipped} (errors)")

    _show_import_errors(result.errors, max_shown=max_errors_shown)


def _show_import_errors(errors: list[str], *, max_shown: int) -> None:
    """Display import errors with truncation."""
    if not errors:
        return

    typer.echo("\n⚠ Errors encountered:", err=True)
    for error in errors[:max_shown]:
        typer.echo(f"  - {error}", err=True)

    if len(errors) > max_shown:
        remaining = len(errors) - max_shown
        typer.echo(f"  ... and {remaining} more errors", err=True)
