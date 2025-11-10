from __future__ import annotations

import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Literal, TypeVar, cast, get_type_hints

import click
import typer

from tasky_cli.context import CLIContext, ensure_cli_context
from tasky_settings import ProjectInitialisationError

F = TypeVar("F", bound=Callable[..., Any])
ErrorHandlers = Sequence[tuple[type[BaseException], int]]
CommandMiddleware = Callable[[CLIContext, str, Callable[[], Any]], Any]
CommandPhase = Literal["start", "success", "error", "exit"]
CommandObserver = Callable[["CommandEvent"], None]

_command_middlewares: list[CommandMiddleware] = []
_command_observers: list[CommandObserver] = []


@dataclass(frozen=True)
class CommandEvent:
    name: str
    phase: CommandPhase
    context: CLIContext
    started_at: datetime
    finished_at: datetime | None
    duration_ms: float | None
    error: BaseException | None
    exit_code: int | None
    result: Any | None = None


def register_command_middleware(middleware: CommandMiddleware) -> None:
    """Append a middleware that wraps every command invocation."""

    _command_middlewares.append(middleware)


def set_command_middlewares(middlewares: Sequence[CommandMiddleware]) -> None:
    """Replace the middleware pipeline (mainly for tests)."""

    _command_middlewares.clear()
    _command_middlewares.extend(middlewares)


def clear_command_middlewares() -> None:
    _command_middlewares.clear()


def register_command_observer(observer: CommandObserver) -> None:
    """Append an observer that receives command lifecycle events."""

    _command_observers.append(observer)


def set_command_observers(observers: Sequence[CommandObserver]) -> None:
    """Replace the observer list (mainly for tests)."""

    _command_observers.clear()
    _command_observers.extend(observers)


def clear_command_observers() -> None:
    _command_observers.clear()


def command_action(
    *,
    requires_project: bool = False,
    handled_errors: ErrorHandlers | None = None,
) -> Callable[[F], F]:
    """
    Decorator to wrap Typer commands with common error handling and preconditions.
    """

    def decorator(func: F) -> F:
        return cast(
            F,
            _wrap_command(func, requires_project=requires_project, handlers=handled_errors),
        )

    return decorator


def _wrap_command(
    func: Callable[..., Any],
    *,
    requires_project: bool,
    handlers: ErrorHandlers | None,
) -> Callable[..., Any]:
    signature = inspect.signature(func)
    type_hints = get_type_hints(
        func,
        globalns=getattr(func, "__globals__", None),
        localns=None,
        include_extras=True,
    )
    adjusted_signature, context_parameter = _inject_typer_context(
        signature,
        func,
        type_hints,
    )

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        cli_context, remaining_args = _resolve_cli_context(args)
        if requires_project:
            _ensure_project_ready(cli_context)

        def handler() -> Any:
            return func(cli_context, *remaining_args, **kwargs)
        return _call_with_handling(
            lambda: _invoke_with_middlewares(cli_context, func.__name__, handler),
            handlers,
            cli_context,
            func.__name__,
        )

    wrapper.__signature__ = adjusted_signature
    wrapper.__annotations__ = _copy_annotations_without_context(type_hints, context_parameter.name)
    return wrapper


def _resolve_cli_context(args: tuple[Any, ...]) -> tuple[CLIContext, tuple[Any, ...]]:
    if args and isinstance(args[0], CLIContext):
        return args[0], args[1:]
    ctx = cast(typer.Context, click.get_current_context())
    return ensure_cli_context(ctx), args


def _call_with_handling(
    call: Callable[[], Any],
    handlers: ErrorHandlers | None,
    context: CLIContext,
    command_name: str,
) -> Any:
    started_at = _utcnow()
    _notify_observers(
        CommandEvent(
            name=command_name,
            phase="start",
            context=context,
            started_at=started_at,
            finished_at=None,
            duration_ms=None,
            error=None,
            exit_code=None,
        )
    )
    try:
        result = call()
    except typer.Exit as exit_exc:
        finished_at = _utcnow()
        _notify_observers(
            CommandEvent(
                name=command_name,
                phase="exit",
                context=context,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=_duration_ms(started_at, finished_at),
                error=None,
                exit_code=exit_exc.exit_code,
            )
        )
        raise
    except Exception as exc:  # noqa: BLE001
        exit_code = _resolve_exit_code(exc, handlers)
        finished_at = _utcnow()
        _notify_observers(
            CommandEvent(
                name=command_name,
                phase="error",
                context=context,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=_duration_ms(started_at, finished_at),
                error=exc,
                exit_code=exit_code,
            )
        )
        if exit_code is None:
            raise
        context.console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=exit_code) from exc
    finished_at = _utcnow()
    event = CommandEvent(
        name=command_name,
        phase="success",
        context=context,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=_duration_ms(started_at, finished_at),
        error=None,
        exit_code=0,
        result=result,
    )
    _notify_observers(event)
    return result


def _ensure_project_ready(context: CLIContext) -> None:
    try:
        context.settings().ensure_project_initialised()
    except ProjectInitialisationError as exc:
        context.console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _resolve_exit_code(
    exc: BaseException,
    handlers: ErrorHandlers | None,
) -> int | None:
    if not handlers:
        return None
    for exc_type, exit_code in handlers:
        if isinstance(exc, exc_type):
            return exit_code
    return None


def _invoke_with_middlewares(
    context: CLIContext,
    command_name: str,
    call: Callable[[], Any],
) -> Any:
    def runner(index: int) -> Any:
        if index >= len(_command_middlewares):
            return call()
        middleware = _command_middlewares[index]
        return middleware(context, command_name, lambda: runner(index + 1))

    return runner(0)


def _copy_annotations_without_context(
    annotations: dict[str, Any],
    context_name: str,
) -> dict[str, Any]:
    annotations = dict(annotations)
    annotations.pop(context_name, None)
    return annotations


def _inject_typer_context(
    sig: inspect.Signature,
    func: Callable[..., Any],
    type_hints: dict[str, Any],
) -> tuple[inspect.Signature, inspect.Parameter]:
    params = list(sig.parameters.values())
    if not params:
        raise TypeError(
            f"Command '{func.__name__}' must accept a CLIContext as the first argument."
        )
    first = params.pop(0)
    annotation = type_hints.get(first.name, first.annotation)
    allowed = {
        CLIContext,
        "CLIContext",
        "tasky_cli.context.CLIContext",
    }
    if annotation is inspect._empty:
        raise TypeError(
            f"Command '{func.__name__}' must annotate the first parameter with CLIContext."
        )
    if annotation not in allowed:
        raise TypeError(
            f"Command '{func.__name__}' first parameter must be a CLIContext; "
            f"got {first.annotation!r}."
        )
    adjusted_params = [
        param.replace(annotation=type_hints.get(param.name, param.annotation))
        for param in params
    ]
    return sig.replace(parameters=adjusted_params), first


def structured_logging_middleware(
    context: CLIContext,
    command_name: str,
    call: Callable[[], Any],
) -> Any:
    if not context.verbose:
        return call()
    started_at = _utcnow()
    _log_command_line(
        context,
        command_name,
        status="start",
        started_at=started_at,
    )
    try:
        result = call()
    except typer.Exit as exit_exc:
        _log_command_line(
            context,
            command_name,
            status="exit",
            started_at=started_at,
            exit_code=exit_exc.exit_code,
        )
        raise
    except Exception:
        _log_command_line(
            context,
            command_name,
            status="error",
            started_at=started_at,
        )
        raise
    _log_command_line(
        context,
        command_name,
        status="success",
        started_at=started_at,
    )
    return result


def _log_command_line(
    context: CLIContext,
    command_name: str,
    *,
    status: str,
    started_at: datetime,
    exit_code: int | None = None,
) -> None:
    finished_at = _utcnow()
    duration_ms = (
        0.0 if status == "start" else _duration_ms(started_at, finished_at)
    )
    timestamp = finished_at.isoformat()
    parts = [
        f"[dim]{timestamp}[/dim]",
        f"command={command_name}",
        f"status={status}",
        f"duration_ms={duration_ms:.1f}",
    ]
    if exit_code is not None:
        parts.append(f"exit_code={exit_code}")
    context.console.print(" ".join(parts))


def _notify_observers(event: CommandEvent) -> None:
    for observer in list(_command_observers):
        try:
            observer(event)
        except Exception:  # noqa: BLE001
            continue


def _duration_ms(started_at: datetime, finished_at: datetime) -> float:
    return (finished_at - started_at).total_seconds() * 1000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
