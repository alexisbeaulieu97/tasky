"""Commands related to task management in Tasky CLI."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import TypeVar, cast
from uuid import UUID

import click
import typer
from tasky_hooks.dispatcher import get_dispatcher
from tasky_hooks.errors import format_error_for_cli
from tasky_hooks.handlers import echo_handler, logging_handler
from tasky_hooks.loader import load_user_hooks
from tasky_settings import create_task_service, get_project_registry_service
from tasky_settings.factory import find_project_root
from tasky_tasks import (
    ImportResult,
    TaskFilter,
    TaskImportExportService,
    TaskModel,
)
from tasky_tasks.enums import TaskStatus
from tasky_tasks.service import TaskService

from tasky_cli.error_dispatcher import ErrorDispatcher
from tasky_cli.validators import date_validator, status_validator, task_id_validator

task_app = typer.Typer(no_args_is_help=True)

F = TypeVar("F", bound=Callable[..., object])

logger = logging.getLogger(__name__)

_VERBOSE_KEY = "verbose"
_VERBOSE_HOOKS_KEY = "verbose_hooks"
_NO_HOOKS_KEY = "no_hooks"
_QUIET_KEY = "quiet"


@task_app.callback()
def task_app_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--verbose",
        "-v",
        help="Show detailed error information, including stack traces.",
    ),
    verbose_hooks: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--verbose-hooks",
        help="Show detailed hook execution information.",
    ),
    no_hooks: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--no-hooks",
        help="Disable all hook execution.",
    ),
    quiet: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--quiet",
        "-q",
        help="Suppress hook console output.",
    ),
) -> None:
    """Configure task command context."""
    ctx.ensure_object(dict)
    ctx.obj[_VERBOSE_KEY] = verbose
    ctx.obj[_VERBOSE_HOOKS_KEY] = verbose_hooks
    ctx.obj[_NO_HOOKS_KEY] = no_hooks
    ctx.obj[_QUIET_KEY] = quiet


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
        except Exception as exc:  # pragma: no cover - defensive catch-all
            dispatcher = ErrorDispatcher()
            result = dispatcher.dispatch(exc, verbose=verbose)
            message = format_error_for_cli(result)
            typer.echo(message, err=True)
            raise typer.Exit(result.exit_code) from exc

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
    # Validate UUID format using TaskIdValidator
    result = task_id_validator.validate(task_id)
    if not result.is_valid:
        typer.echo(result.error_message, err=True)
        raise typer.Exit(1)

    # Only create service after UUID is validated
    service = _get_service()

    return service, result.value  # type: ignore[return-value]


def _validate_status_filter(status: str | None) -> TaskStatus | None:
    """Validate and convert status string to TaskStatus enum.

    Args:
        status: Status string from command-line argument, or None.

    Returns:
        TaskStatus enum value if valid, None if status was None.

    Raises:
        typer.Exit: If status is invalid.

    """
    if status is None:
        return None

    result = status_validator.validate(status)
    if not result.is_valid:
        typer.echo(result.error_message, err=True)
        raise typer.Exit(1)

    return result.value  # type: ignore[return-value]


def _parse_date_filter(date_str: str, *, inclusive_end: bool = False) -> datetime:
    """Parse and validate a date string for filtering.

    Args:
        date_str: Date string in ISO 8601 format (YYYY-MM-DD).
        inclusive_end: If True, add 1 day to make the date inclusive of the entire day.
                      Used for --created-before to include all of the specified date.

    Returns:
        A timezone-aware datetime object (UTC midnight).

    Raises:
        typer.Exit: If the date format is invalid or cannot be parsed.

    """
    # Validate date format using DateValidator
    result = date_validator.validate(date_str)
    if not result.is_valid:
        typer.echo(result.error_message, err=True)
        raise typer.Exit(1)

    # For --created-before, add 1 day to make the exclusive < check
    # inclusive of the entire day (user expects --created-before 2025-12-31
    # to include all of Dec 31)
    if inclusive_end:
        return result.value + timedelta(days=1)  # type: ignore[operator, return-value]

    return result.value  # type: ignore[return-value]


def _build_task_list_filter(
    task_status: TaskStatus | None,
    created_after_dt: datetime | None,
    created_before_dt: datetime | None,
    search: str | None,
) -> tuple[TaskFilter | None, bool]:
    """Build a TaskFilter from command-line arguments.

    Args:
        task_status: Status to filter by, or None.
        created_after_dt: Start date for filtering, or None.
        created_before_dt: End date for filtering, or None.
        search: Text to search for in task name/details, or None.
                Empty strings are normalized to None.

    Returns:
        A tuple of (filter_object, has_filters) where:
        - filter_object is a TaskFilter if any filters are active, else None
        - has_filters is True if any filter arguments were provided

    """
    # Normalize empty search to None (per spec: empty search = no filter)
    normalized_search = None if (search is None or not search.strip()) else search

    has_filters = (
        task_status is not None
        or created_after_dt is not None
        or created_before_dt is not None
        or normalized_search is not None
    )

    if has_filters:
        return (
            TaskFilter(
                statuses=[task_status] if task_status is not None else None,
                created_after=created_after_dt,
                created_before=created_before_dt,
                name_contains=normalized_search,
            ),
            True,
        )

    return None, False


def _render_task_list_summary(tasks: list[TaskModel], *, has_filters: bool) -> None:
    """Render the summary line after displaying tasks.

    Args:
        tasks: List of tasks to summarize.
        has_filters: Whether filters were applied to the task list.

    """
    if not tasks:
        # Show filter-specific message when filtering, generic message otherwise
        if has_filters:
            typer.echo("No matching tasks found")
        else:
            typer.echo("No tasks to display")
        return

    # Count tasks by status
    pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    completed_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    cancelled_count = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)

    # Display summary line
    task_word = "task" if len(tasks) == 1 else "tasks"
    typer.echo(
        f"\nShowing {len(tasks)} {task_word} "
        f"({pending_count} pending, {completed_count} completed, "
        f"{cancelled_count} cancelled)",
    )


def _render_task_list(tasks: list[TaskModel], *, show_timestamps: bool = False) -> None:
    """Render the list of tasks with status indicators.

    Args:
        tasks: List of tasks to display (will be sorted by status).
        show_timestamps: Whether to show created_at and updated_at timestamps.

    """
    # Sort tasks by status: pending → completed → cancelled
    status_order = {TaskStatus.PENDING: 0, TaskStatus.COMPLETED: 1, TaskStatus.CANCELLED: 2}
    sorted_tasks = sorted(tasks, key=lambda t: status_order[t.status])

    # Display tasks with status indicators
    for task in sorted_tasks:
        # Map status to indicator
        status_indicator = _get_status_indicator(task.status)
        typer.echo(f"{status_indicator} {task.task_id} {task.name} - {task.details}")

        # Show timestamps if requested
        if show_timestamps:
            created = task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            updated = task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            typer.echo(f"  Created: {created} | Modified: {updated}")


@task_app.command(name="list")
@with_task_error_handling
def list_command(
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
    task_status = _validate_status_filter(status)

    # Parse and validate date arguments
    created_after_dt: datetime | None = None
    created_before_dt: datetime | None = None

    if created_after is not None:
        created_after_dt = _parse_date_filter(created_after)

    if created_before is not None:
        created_before_dt = _parse_date_filter(created_before, inclusive_end=True)

    # Only create service after validating input
    service = _get_service()

    # Build filter and fetch tasks
    task_filter, has_filters = _build_task_list_filter(
        task_status,
        created_after_dt,
        created_before_dt,
        search,
    )

    tasks = service.find_tasks(task_filter) if task_filter is not None else service.get_all_tasks()

    # Handle empty results early
    if not tasks:
        _render_task_list_summary(tasks, has_filters=has_filters)
        return

    # Display tasks with status indicators
    _render_task_list(tasks, show_timestamps=long)

    # Display summary line
    _render_task_list_summary(tasks, has_filters=has_filters)


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

    # Update project last accessed timestamp
    _update_project_last_accessed()


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

    # Update project last accessed timestamp
    _update_project_last_accessed()


def _get_service() -> TaskService:
    """Get or create a task service for the current project.

    Returns:
        Configured TaskService instance

    Raises:
        ProjectNotFoundError: If no project found
        KeyError: If configured backend is not registered

    """
    return create_task_service()


def _update_project_last_accessed() -> None:
    """Update the last accessed timestamp for the current project in the registry.

    This is called after any task operation to keep the registry's
    last_accessed timestamp current.

    """
    try:
        project_root = find_project_root()
        registry_service = get_project_registry_service()
        registry_service.update_last_accessed(project_root)
    except Exception as exc:  # noqa: BLE001
        # Silently ignore registry update failures to not disrupt task operations
        # The registry is a secondary feature and should not block core functionality
        logger.debug("Failed to update project last_accessed timestamp: %s", exc)


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


def _is_verbose_hooks(ctx: typer.Context | None) -> bool:
    current = ctx
    while current is not None:
        obj: object = current.obj
        if isinstance(obj, dict):
            value: bool = bool(obj.get(_VERBOSE_HOOKS_KEY, False))
            return value
        current = current.parent
    return False


def _get_context_value(ctx: typer.Context | None, key: str) -> bool:
    current = ctx
    while current is not None:
        obj: object = current.obj
        if isinstance(obj, dict):
            value = obj.get(key)
            if value is not None:
                return bool(value)
        current = current.parent
    return False


def _get_service() -> TaskService:
    """Get or create a task service for the current project.

    Returns:
        Configured TaskService instance

    Raises:
        ProjectNotFoundError: If no project found
        KeyError: If configured backend is not registered

    """
    ctx = click.get_current_context(silent=True)
    typer_ctx = _convert_context(ctx) if ctx else None

    # Check for --no-hooks
    if _get_context_value(typer_ctx, _NO_HOOKS_KEY):
        return create_task_service(dispatcher=None)

    # Initialize hooks
    dispatcher = get_dispatcher()

    # Load user hooks
    load_user_hooks()

    # Register default logging handler (always)
    # Note: In a long-running process, we'd need to be careful about duplicates,
    # but CLI commands run once.
    dispatcher.register("*", logging_handler)

    # Register echo handler if --verbose-hooks is set
    if _get_context_value(typer_ctx, _VERBOSE_HOOKS_KEY) and not _get_context_value(
        typer_ctx, _QUIET_KEY,
    ):
        dispatcher.register("*", echo_handler)

    return create_task_service(dispatcher=dispatcher)


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

    # Update project last accessed timestamp
    _update_project_last_accessed()


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

    # Update project last accessed timestamp
    _update_project_last_accessed()


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

    # Update project last accessed timestamp
    _update_project_last_accessed()


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
