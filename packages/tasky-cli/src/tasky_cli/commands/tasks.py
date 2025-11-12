"""Commands related to task management in Tasky CLI."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import NoReturn, TypeVar, cast
from uuid import UUID

import click
import typer
from tasky_storage.backends.json.repository import JsonTaskRepository
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
    - Storage path validation
    - UUID parsing with error handling
    - Task service initialization

    Args:
        task_id: The task ID string from CLI input.

    Returns:
        Tuple of (TaskService instance, parsed UUID).

    Raises:
        typer.Exit: On validation errors (storage missing or invalid UUID).

    """
    storage_path = _storage_path()

    if not storage_path.exists():
        typer.echo("No tasks found. Initialize a project first.", err=True)
        raise typer.Exit(1)

    try:
        uuid = UUID(task_id)
    except ValueError as exc:
        typer.echo(f"Invalid task ID format: {task_id}", err=True)
        raise typer.Exit(1) from exc

    service = _create_task_service(storage_path)
    return service, uuid


@task_app.command(name="list")
@with_task_error_handling
def list_command() -> None:
    """List all tasks."""
    storage_path = _storage_path()

    if not storage_path.exists():
        typer.echo(f"No tasks found in {storage_path}")
        return

    service = _create_task_service(storage_path)
    tasks = service.get_all_tasks()

    if not tasks:
        typer.echo("No tasks recorded yet.")
        return

    for task in tasks:
        typer.echo(f"{task.name} - {task.details}")


def _storage_path() -> Path:
    return Path(".tasky/tasks.json")


def _create_task_service(storage_path: Path) -> TaskService:
    repository = JsonTaskRepository.from_path(storage_path)
    return TaskService(repository)


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
        f"Task is already completed. "
        f"Use 'tasky task reopen {task_id}' if you want to make changes."
    )
    cancelled_suggestion = (
        f"Task is already cancelled. "
        f"Use 'tasky task reopen {task_id}' if you want to make changes."
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
    if isinstance(exc, TaskDomainError):
        _handle_task_domain_error(exc, verbose=verbose)
    elif isinstance(exc, StorageError):
        _handle_storage_error(exc, verbose=verbose)
    else:
        _handle_unexpected_error(exc, verbose=verbose)


def _handle_task_domain_error(exc: TaskDomainError, *, verbose: bool) -> NoReturn:
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


def _handle_storage_error(exc: StorageError, *, verbose: bool) -> NoReturn:
    _render_error(
        "Storage failure encountered. Verify project initialization and file permissions.",
        suggestion="Run 'tasky project init' or check the .tasky directory.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(3) from exc


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
