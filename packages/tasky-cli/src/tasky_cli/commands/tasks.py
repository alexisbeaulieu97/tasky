"""Commands related to task management in Tasky CLI."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import NoReturn, TypeVar, cast

import typer
from click import get_current_context
from tasky_storage.backends.json.repository import JsonTaskRepository
from tasky_storage.errors import StorageError
from tasky_tasks import (
    InvalidStateTransitionError,
    TaskDomainError,
    TaskNotFoundError,
    TaskValidationError,
)
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
        ctx = get_current_context(silent=True)
        verbose = _is_verbose(ctx)

        try:
            return func(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch-all  # noqa: BLE001
            _dispatch_exception(exc, verbose=verbose)

    return cast("F", wrapper)


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


def _is_verbose(ctx: typer.Context | None) -> bool:
    current = ctx
    while current is not None:
        obj = current.obj
        if isinstance(obj, dict) and _VERBOSE_KEY in obj:
            return bool(obj[_VERBOSE_KEY])
        current = current.parent
    return False


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
        _render_error(
            f"Cannot transition task '{exc.task_id}' from {exc.from_status} to {exc.to_status}.",
            suggestion="Use 'tasky task list' to inspect the current status before retrying.",
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
