"""Commands related to task management in Tasky CLI."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from functools import wraps
from typing import NoReturn, TypeVar, cast
from uuid import UUID

import click
import typer
from pydantic import ValidationError as PydanticValidationError
from tasky_settings import ProjectNotFoundError, create_task_service
from tasky_storage.errors import StorageError
from tasky_tasks import (
    InvalidStateTransitionError,
    TaskDomainError,
    TaskNotFoundError,
    TaskValidationError,
)
from tasky_tasks.models import TaskStatus
from tasky_tasks.service import TaskService

task_app = typer.Typer(no_args_is_help=True)

F = TypeVar("F", bound=Callable[..., object])
Handler = Callable[[Exception, bool], NoReturn]
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
    - Project validation (via error dispatcher)
    - UUID parsing with error handling
    - Task service initialization

    Args:
        task_id: The task ID string from CLI input.

    Returns:
        Tuple of (TaskService instance, parsed UUID).

    Raises:
        ProjectNotFoundError: If no project found (caught by error dispatcher)
        KeyError: If backend not registered (caught by error dispatcher)
        typer.Exit: On invalid UUID format

    """
    service = _get_service()

    try:
        uuid = UUID(task_id)
    except ValueError as exc:
        typer.echo(f"Invalid task ID format: {task_id}", err=True)
        raise typer.Exit(1) from exc

    return service, uuid


@task_app.command(name="list")
@with_task_error_handling
def list_command(  # noqa: C901
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter tasks by status (pending, completed, cancelled).",
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

    Example:
        $ tasky task list
        ○ 550e8400-e29b-41d4-a716-446655440000 Buy groceries - Get milk and eggs
        ✓ 550e8400-e29b-41d4-a716-446655440001 Review PR - Check code quality

        Showing 2 tasks (1 pending, 1 completed, 0 cancelled)

        $ tasky task list --long
        ○ 550e8400-e29b-41d4-a716-446655440000 Buy groceries - Get milk and eggs
          Created: 2025-11-12T10:30:00Z | Modified: 2025-11-12T10:30:00Z

        Showing 1 task (1 pending, 0 completed, 0 cancelled)

    """
    service = _get_service()

    # Validate and filter by status if provided
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
        tasks = service.get_tasks_by_status(task_status)
    else:
        tasks = service.get_all_tasks()

    if not tasks:
        # Show status-specific message when filtering, generic message otherwise
        if task_status is not None:
            typer.echo(f"No {task_status.value} tasks found.")
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
            handler(exc, verbose)  # Call with positional args as per Handler type

    # Fallback for unexpected errors
    _handle_unexpected_error(exc, verbose)


def _handle_task_domain_error(exc: TaskDomainError, verbose: bool) -> NoReturn:
    if isinstance(exc, TaskNotFoundError):
        _render_error(
            f"Task '{exc.task_id}' not found.",
            suggestion="Run 'tasky task list' to view available tasks.",
            verbose=verbose,
            exc=exc,
        )
    elif isinstance(exc, TaskValidationError):
        suggestion = None
        if getattr(exc, "field", None):
            suggestion = f"Check the value provided for '{exc.field}'."
        message = str(exc) or "Task validation failed."
        _render_error(message, suggestion=suggestion, verbose=verbose, exc=exc)
    elif isinstance(exc, InvalidStateTransitionError):
        suggestion = _suggest_transition(
            from_status=exc.from_status,
            to_status=exc.to_status,
            task_id=str(exc.task_id),
        )
        _render_error(
            f"Cannot transition from {exc.from_status} to {exc.to_status}.",
            suggestion=suggestion,
            verbose=verbose,
            exc=exc,
        )
    else:
        _render_error(str(exc) or "Task operation failed.", verbose=verbose, exc=exc)

    raise typer.Exit(1) from exc


def _handle_storage_error(exc: StorageError, verbose: bool) -> NoReturn:
    _render_error(
        "Storage failure encountered. Verify project initialization and file permissions.",
        suggestion="Run 'tasky project init' or check the .tasky directory.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(3) from exc


def _handle_project_not_found_error(exc: ProjectNotFoundError, verbose: bool) -> NoReturn:
    _render_error(
        "No project found in current directory.",
        suggestion="Run 'tasky project init' to create a project.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from exc


def _handle_backend_not_registered_error(exc: KeyError, verbose: bool) -> NoReturn:
    """Render backend registry errors with actionable guidance."""
    details = exc.args[0] if exc.args else "Configured backend is not registered."
    _render_error(
        str(details),
        suggestion="Update .tasky/config.toml or re-run 'tasky project init' with a valid backend.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from exc


def _handle_pydantic_validation_error(exc: PydanticValidationError, verbose: bool) -> NoReturn:
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


def _handle_unexpected_error(exc: Exception, verbose: bool) -> NoReturn:
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
