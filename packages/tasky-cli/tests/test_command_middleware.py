from __future__ import annotations

from typer import Context, Typer
from typer.testing import CliRunner

from tasky_cli.commands.common import (
    clear_command_middlewares,
    clear_command_observers,
    command_action,
    register_command_middleware,
    register_command_observer,
    structured_logging_middleware,
)
from tasky_cli.context import CLIContext, ensure_cli_context


runner = CliRunner()


def test_command_action_injects_cli_context() -> None:
    app = Typer()

    @app.callback()
    def _root() -> None:
        # Typer 0.20 treats single-command apps as bare commands, so ensure we have
        # a callback to keep the subcommand semantics used by the real CLI.
        pass

    captured: list[CLIContext] = []
    clear_command_middlewares()

    @command_action()
    def sample_command(context: CLIContext) -> None:
        captured.append(context)

    app.command("sample")(sample_command)

    result = runner.invoke(app, ["sample"])

    assert result.exit_code == 0
    assert len(captured) == 1
    assert isinstance(captured[0], CLIContext)


def test_command_middlewares_wrap_handler() -> None:
    app = Typer()

    @app.callback()
    def _root() -> None:
        pass

    events: list[str] = []

    def logging_middleware(context: CLIContext, name: str, call):  # type: ignore[override]
        events.append(f"before:{name}")
        result = call()
        events.append(f"after:{name}")
        return result

    clear_command_middlewares()
    register_command_middleware(logging_middleware)

    @command_action()
    def sample_command(context: CLIContext) -> None:
        events.append("handler")

    app.command("sample")(sample_command)

    try:
        result = runner.invoke(app, ["sample"])
    finally:
        clear_command_middlewares()

    assert result.exit_code == 0
    assert events == ["before:sample_command", "handler", "after:sample_command"]


def test_command_observers_receive_start_and_success_events() -> None:
    app = Typer()

    @app.callback()
    def _root() -> None:
        pass

    clear_command_observers()
    clear_command_middlewares()

    phases: list[str] = []

    def observer(event) -> None:
        phases.append(event.phase)

    register_command_observer(observer)

    @command_action()
    def sample_command(context: CLIContext) -> None:
        return None

    app.command("sample")(sample_command)

    try:
        result = runner.invoke(app, ["sample"])
    finally:
        clear_command_observers()

    assert result.exit_code == 0
    assert phases == ["start", "success"]


def test_command_observers_capture_errors_with_exit_codes() -> None:
    app = Typer()

    @app.callback()
    def _root() -> None:
        pass

    clear_command_observers()
    clear_command_middlewares()
    captured: list[tuple[str, int | None]] = []

    def observer(event) -> None:
        captured.append((event.phase, event.exit_code))

    register_command_observer(observer)

    @command_action(handled_errors=[(ValueError, 2)])
    def sample_command(context: CLIContext) -> None:
        raise ValueError("boom")

    app.command("sample")(sample_command)

    try:
        result = runner.invoke(app, ["sample"])
    finally:
        clear_command_observers()

    assert result.exit_code == 2
    assert captured[-1] == ("error", 2)


def test_structured_logging_middleware_is_quiet_without_verbose() -> None:
    app = Typer()

    @app.callback()
    def _root() -> None:
        pass

    clear_command_middlewares()
    register_command_middleware(structured_logging_middleware)

    @command_action()
    def sample_command(context: CLIContext) -> None:
        return None

    app.command("sample")(sample_command)

    try:
        result = runner.invoke(app, ["sample"])
    finally:
        clear_command_middlewares()

    assert result.exit_code == 0
    assert "status=" not in result.stdout


def test_structured_logging_middleware_prints_start_and_finish_when_verbose() -> None:
    app = Typer()

    @app.callback()
    def _root(ctx: Context) -> None:
        ensure_cli_context(ctx, verbose=True)

    clear_command_middlewares()
    register_command_middleware(structured_logging_middleware)

    @command_action()
    def sample_command(context: CLIContext) -> None:
        return None

    app.command("sample")(sample_command)

    try:
        result = runner.invoke(app, ["sample"])
    finally:
        clear_command_middlewares()

    assert result.exit_code == 0
    assert "status=start" in result.stdout
    assert "status=success" in result.stdout
