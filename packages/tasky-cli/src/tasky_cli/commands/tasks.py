from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
from tasky_core import (
    TaskImportError,
    TaskNotFoundError,
    TaskUseCaseError,
    TaskValidationError,
    get_import_strategy,
    load_tasks_from_json,
)
from tasky_core.hooks import (
    HookConfigurationError,
    HookExecutionError,
)
from tasky_models import Task

from tasky_cli.context import CLIContext, ensure_cli_context, get_cli_context
from tasky_cli.ui.tasks import build_task_table

from .common import command_action

task_app = typer.Typer(
    help="Manage tasks inside the current project.",
    add_completion=False,
    no_args_is_help=True,
)

StrategyLiteral = Literal["append", "replace", "merge"]

ExportOutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        help="Write exported tasks to OUTPUT (defaults to STDOUT).",
        dir_okay=False,
    ),
]


@task_app.callback(invoke_without_command=True)
def task_group_callback(ctx: typer.Context) -> None:
    """Task management commands."""
    ensure_cli_context(ctx)
    if ctx.invoked_subcommand is None:
        context = get_cli_context(ctx)
        _render_task_list(context)


@task_app.command("list")
@command_action(requires_project=True, handled_errors=[(TaskUseCaseError, 1)])
def task_list_command(context: CLIContext) -> None:
    """List all stored tasks in a table."""
    _render_task_list(context)


@task_app.command("add")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskValidationError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_add_command(
    context: CLIContext,
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Title shown for the new task in listings and exports.",
        ),
    ],
    details: Annotated[
        str,
        typer.Option(
            "--details",
            "-d",
            help="Free-form description that explains the work to complete.",
        ),
    ],
    parent: Annotated[
        str | None,
        typer.Option(
            "--parent",
            help="ID of the parent task to nest under (leave empty for top level).",
        ),
    ] = None,
) -> None:
    """Create a new task."""
    service = context.task_service()
    task = service.create(name=name, details=details, parent_id=parent)
    context.console.print(f"[green]Created[/green] {task.name!r} (id={task.task_id})")


@task_app.command("remove")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskValidationError, 2),
        (TaskNotFoundError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_remove_command(
    context: CLIContext,
    task_id: Annotated[
        str,
        typer.Argument(
            metavar="TASK_ID",
            help="ID of the task to delete from the current project.",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Delete without asking for confirmation.",
        ),
    ] = False,
) -> None:
    """Remove a task by its identifier."""
    console = context.console
    if not force:
        confirmed = typer.confirm(f"Delete task '{task_id}'?", default=False)
        if not confirmed:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    service = context.task_service()
    task = service.remove(task_id)

    console.print(f"[green]Removed[/green] {task.name!r} (id={task.task_id})")


@task_app.command("complete")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskValidationError, 2),
        (TaskNotFoundError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_complete_command(
    context: CLIContext,
    task_id: Annotated[
        str,
        typer.Argument(
            metavar="TASK_ID",
            help="ID of the task to mark as completed.",
        ),
    ],
) -> None:
    """Mark a task as completed."""
    service = context.task_service()
    task = service.complete(task_id)
    context.console.print(f"[green]Completed[/green] {task.name!r} (id={task.task_id})")


@task_app.command("reopen")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskValidationError, 2),
        (TaskNotFoundError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_reopen_command(
    context: CLIContext,
    task_id: Annotated[
        str,
        typer.Argument(
            metavar="TASK_ID",
            help="ID of the task to reopen so it appears as pending.",
        ),
    ],
) -> None:
    """Mark a task as incomplete."""
    service = context.task_service()
    task = service.reopen(task_id)
    context.console.print(f"[green]Reopened[/green] {task.name!r} (id={task.task_id})")


@task_app.command("update")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskValidationError, 2),
        (TaskNotFoundError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_update_command(
    context: CLIContext,
    task_id: Annotated[
        str,
        typer.Argument(
            metavar="TASK_ID",
            help="ID of the task to rename or update details for.",
        ),
    ],
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Provide to rename the task while keeping its history.",
        ),
    ] = None,
    details: Annotated[
        str | None,
        typer.Option(
            "--details",
            "-d",
            help="Provide to replace the task description with new guidance.",
        ),
    ] = None,
) -> None:
    """Update task name/details."""
    service = context.task_service()
    task = service.update(task_id, name=name, details=details)
    context.console.print(f"[green]Updated[/green] {task.name!r} (id={task.task_id})")


@task_app.command("import")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskImportError, 2),
        (HookConfigurationError, 3),
        (HookExecutionError, 3),
        (TaskUseCaseError, 1),
    ],
)
def task_import_command(
    context: CLIContext,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            help="Path to a JSON file containing tasks to import (reads STDIN when omitted).",
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    strategy: Annotated[
        StrategyLiteral,
        typer.Option(
            "--strategy",
            "-s",
            help=(
                "Decide how incoming tasks interact with existing ones "
                "(append keeps everything, replace overwrites, merge updates by ID)."
            ),
            case_sensitive=False,
            show_default=True,
        ),
    ] = "append",
) -> None:
    """Import tasks from a JSON payload."""
    source = _read_import_source(file)
    tasks_to_add = load_tasks_from_json(source)

    strategy_impl = get_import_strategy(strategy)
    service = context.task_service()
    service.import_tasks(tasks_to_add, strategy_impl)

    message = {
        "replace": "[green]Replaced[/green]",
        "merge": "[green]Merged[/green]",
        "append": "[green]Imported[/green]",
    }.get(strategy_impl.name, "[green]Imported[/green]")
    context.console.print(f"{message} {len(tasks_to_add)} task(s).")


@task_app.command("export")
@command_action(
    requires_project=True,
    handled_errors=[
        (TaskUseCaseError, 1),
    ],
)
def task_export_command(
    context: CLIContext,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write the exported tasks to this file instead of STDOUT.",
            dir_okay=False,
        ),
    ] = None,
    completed: Annotated[
        bool,
        typer.Option("--completed", help="Only export completed tasks."),
    ] = False,
    pending: Annotated[
        bool,
        typer.Option("--pending", help="Only export pending tasks."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite the output file if it already exists.",
        ),
    ] = False,
) -> None:
    """Export tasks to JSON."""
    if completed and pending:
        raise typer.BadParameter("Use at most one of --completed/--pending.")
    service = context.task_service()
    tasks = service.export()
    filtered = _filter_export_tasks(tasks, completed=completed, pending=pending)
    payload = json.dumps([task.model_dump(mode="json") for task in filtered], indent=2)
    if output is None:
        typer.echo(payload)
        return
    path = output.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise typer.BadParameter(
            f"File {path} already exists. Use --force to overwrite.",
            param_hint="--file",
        )
    try:
        path.write_text(payload + "\n", encoding="utf-8")
    except OSError as exc:
        raise TaskUseCaseError(f"Failed to write export file: {path}") from exc
    context.console.print(f"[green]Exported[/green] {len(filtered)} task(s) to {path}")


def _render_task_list(context: CLIContext) -> None:
    service = context.task_service()
    tasks = service.list()

    if not tasks:
        context.console.print("[yellow]No tasks found.[/yellow]")
        raise typer.Exit()

    table = build_task_table(tasks)
    context.console.print(table)


def _read_import_source(file: Path | None) -> str:
    if file is not None:
        try:
            return file.read_text(encoding="utf-8")
        except OSError as exc:
            raise TaskImportError(f"Could not read import file: {file}") from exc
    if sys.stdin.isatty():
        raise TaskImportError("Provide --file or pipe a JSON payload via STDIN.")
    return sys.stdin.read()


def _filter_export_tasks(
    tasks: list[Task],
    *,
    completed: bool,
    pending: bool,
) -> list[Task]:
    if completed:
        return [task for task in tasks if task.completed]
    if pending:
        return [task for task in tasks if not task.completed]
    return tasks
