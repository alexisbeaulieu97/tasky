from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from tasky_cli.context import CLIContext, ensure_cli_context
from tasky_cli.ui.formatting import format_timestamp
from tasky_settings import (
    ProjectAlreadyInitialisedError,
    ProjectConfig,
    ProjectInitialisationError,
    ProjectRegistryError,
    ProjectSettingsError,
)

from .common import command_action

HOOKS_DIRNAME = "hooks"
HOOK_MANIFEST_NAME = "hook.json"
HOOK_TEMPLATE_PACKAGE = "tasky_cli.templates.hooks"

project_app = typer.Typer(
    help="Manage registered Tasky projects.",
    add_completion=False,
    no_args_is_help=True,
)

hooks_app = typer.Typer(
    help="Manage per-project automation hooks.",
    add_completion=False,
    no_args_is_help=True,
)

InitForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        "-f",
        help="Overwrite existing project storage with an empty dataset.",
    ),
]

InitPathArgument = Annotated[
    Path,
    typer.Argument(
        help="Directory to initialise as a Tasky project (defaults to CWD).",
        dir_okay=True,
        file_okay=False,
    ),
]

ProjectPathArgument = Annotated[
    Path,
    typer.Argument(
        help="Project directory to remove from the registry (defaults to CWD).",
        dir_okay=True,
        file_okay=False,
    ),
]

ProjectPathOption = Annotated[
    Path | None,
    typer.Option(
        "--path",
        "-p",
        help="Project directory to inspect (defaults to the current working directory).",
        dir_okay=True,
        file_okay=False,
    ),
]

ConfigSetOption = Annotated[
    list[str] | None,
    typer.Option(
        "--set",
        "-s",
        help="Update config values using KEY=VALUE syntax (e.g., --set tasks_file=tasks.sqlite).",
    ),
]

ForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        "-f",
        help="Apply changes without additional confirmation prompts.",
    ),
]


@project_app.callback()
def project_app_callback(ctx: typer.Context) -> None:
    ensure_cli_context(ctx)


@hooks_app.callback()
def hooks_app_callback(ctx: typer.Context) -> None:
    ensure_cli_context(ctx)


@project_app.command("init")
@command_action()
def init_command(
    context: CLIContext,
    path: InitPathArgument = Path("."),
    force: InitForceOption = False,
) -> None:
    """Initialise a new project."""
    console = context.console
    project_path = path.expanduser()
    project_path.mkdir(parents=True, exist_ok=True)
    project_path = project_path.resolve()
    settings = context.settings()
    already_initialised = settings.is_project_initialised(project_path)
    if already_initialised and not force:
        console.print(
            f"[red]Project at {project_path} is already initialised. Use '--force' to reinitialise.[/red]"
        )
        raise typer.Exit(code=1)

    try:
        settings.initialise_project(project_path, force=force)
    except ProjectAlreadyInitialisedError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    verb = "[yellow]Reinitialised[/yellow]" if already_initialised else "[green]Initialised[/green]"
    console.print(f"{verb} project at {project_path}")


@project_app.command("register")
@command_action()
def project_register_command(
    context: CLIContext,
    path: ProjectPathArgument = Path("."),
) -> None:
    """Register an existing project directory without reinitialising it."""
    console = context.console
    settings = context.settings()
    project_ctx = settings.get_project_context(path)
    metadata_dir = project_ctx.metadata_dir
    config_path = project_ctx.config_path
    if not metadata_dir.exists() or not config_path.exists():
        console.print(
            f"[red]Project metadata missing at {metadata_dir}. Run 'tasky project init' first.[/red]"
        )
        raise typer.Exit(code=1)

    try:
        entry = settings.register_project(project_ctx.project_path)
    except ProjectRegistryError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Registered[/green] project at {entry.path}")


@project_app.command("list")
@command_action()
def project_list_command(
    context: CLIContext,
    include_missing: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Include projects whose directories are missing.",
        ),
    ] = False,
    refresh_progress: Annotated[
        bool,
        typer.Option(
            "--refresh-progress",
            "-r",
            help="Recompute cached progress counts before listing.",
        ),
    ] = False,
) -> None:
    """List registered Tasky projects."""
    console = context.console
    query = context.project_query_service()
    overviews = query.list_overviews(
        include_missing=include_missing,
        refresh_cache=refresh_progress,
    )
    if not overviews:
        console.print("[yellow]No projects registered.[/yellow]")
        raise typer.Exit()

    table = Table(title="Registered Projects", header_style="bold")
    table.add_column("Path", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Progress", style="cyan")
    table.add_column("Updated", style="dim")

    for overview in overviews:
        entry = overview.entry
        path = Path(entry.path)
        status = "[green]available[/green]" if overview.exists else "[red]missing[/red]"
        progress = _progress_label(overview.progress) if overview.exists else "-"
        table.add_row(str(path), status, progress, format_timestamp(entry.updated_at))

    console.print(table)


@project_app.command("prune")
@command_action()
def project_prune_command(
    context: CLIContext,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be pruned without deleting."),
    ] = False,
) -> None:
    """Remove missing projects from the registry."""
    console = context.console
    if dry_run:
        query = context.project_query_service()
        overviews = query.list_overviews(include_missing=True)
        missing = [overview.entry for overview in overviews if not overview.exists]
    else:
        missing = context.settings().prune_missing_projects()
    if not missing:
        console.print("[green]No missing projects to prune.[/green]")
        raise typer.Exit()

    table = Table(
        title="Missing Projects" if dry_run else "Pruned Projects",
        header_style="bold",
    )
    table.add_column("Path", style="magenta")
    table.add_column("Registered", style="dim")
    for entry in missing:
        table.add_row(str(entry.path), format_timestamp(entry.created_at))
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run only. Run without --dry-run to prune.[/yellow]")
    else:
        console.print(f"[green]Removed[/green] {len(missing)} project(s).")


@project_app.command("unregister")
@command_action()
def project_unregister_command(
    context: CLIContext,
    path: ProjectPathArgument = Path("."),
    purge: Annotated[
        bool,
        typer.Option(
            "--purge",
            help="Delete the project's .tasky directory after unregistering.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip interactive confirmation when unregistering a project.",
        ),
    ] = False,
) -> None:
    """Unregister a project and optionally remove its metadata directory."""
    console = context.console
    settings = context.settings()
    project_ctx = settings.get_project_context(path)
    project_path = project_ctx.project_path

    if purge and project_ctx.metadata_dir.exists() and not force:
        confirmed = typer.confirm(
            f"Delete metadata directory '{project_ctx.metadata_dir}'?",
            default=False,
        )
        if not confirmed:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    try:
        settings.unregister_project(project_path, purge=purge)
    except ProjectRegistryError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]Removed[/green] project at {project_path} from the registry"
        + (" and deleted metadata." if purge else ".")
    )


@project_app.command("config")
@command_action(
    requires_project=True,
    handled_errors=[
        (ProjectInitialisationError, 1),
        (ProjectSettingsError, 1),
    ],
)
def project_config_command(
    context: CLIContext,
    project_path: ProjectPathOption = None,
    set_values: ConfigSetOption = None,
    force: ForceOption = False,
) -> None:
    """Inspect or modify the project's .tasky/config.json file."""
    settings = context.settings()
    config = settings.load_project_config(project_path)
    if not set_values:
        _print_config(config, context)
        return
    updates = _parse_config_updates(set_values)
    if not updates:
        context.console.print("[yellow]No configuration changes supplied.[/yellow]")
        return
    updates = _prepare_config_updates(
        config=config,
        updates=updates,
        force=force,
        console=context.console,
    )
    if not updates:
        context.console.print(
            "[yellow]No changes applied (config already matches provided values).[/yellow]"
        )
        return
    updated = settings.update_project_config(
        project_path=project_path,
        updates=updates,
        force=force,
    )
    context.console.print("[green]Updated[/green] project config:")
    _print_config(updated, context)


@hooks_app.command("scaffold")
@command_action(requires_project=True)
def project_hooks_scaffold_command(
    context: CLIContext,
    *,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing hook files."),
    ] = False,
    minimal: Annotated[
        bool,
        typer.Option("--minimal", help="Only create hook.json (skip sample scripts)."),
    ] = False,
) -> None:
    """Bootstrap .tasky/hooks with a manifest and optional sample scripts."""
    console = context.console
    settings = context.settings()
    project_ctx = settings.ensure_project_initialised()
    hooks_dir = project_ctx.metadata_dir / HOOKS_DIRNAME
    manifest_path = hooks_dir / HOOK_MANIFEST_NAME
    sample_files = (
        [] if minimal else [hooks_dir / "sample_pre_add.py", hooks_dir / "sample_post_add.py"]
    )
    existing = [path for path in [manifest_path, *sample_files] if path.exists()]
    if existing and not force:
        formatted = ", ".join(str(path.relative_to(project_ctx.project_path)) for path in existing)
        console.print(
            f"[red]Hook files already exist ({formatted}). Use '--force' to overwrite.[/red]"
        )
        raise typer.Exit(code=1)

    hooks_dir.mkdir(parents=True, exist_ok=True)
    _write_manifest(manifest_path, minimal=minimal)
    created = [manifest_path]

    if not minimal:
        try:
            _write_script(sample_files[0], "sample_pre_add.py.tmpl")
            _write_script(sample_files[1], "sample_post_add.py.tmpl")
        except FileNotFoundError as exc:
            console.print(f"[red]Missing hook template: {exc}[/red]")
            raise typer.Exit(code=1) from exc
        created.extend(sample_files)

    console.print(
        "[green]Scaffolded[/green] hook assets:\n"
        + "\n".join(f"  - {path.relative_to(project_ctx.project_path)}" for path in created)
    )

project_app.add_typer(hooks_app, name="hooks")


def _write_manifest(path: Path, *, minimal: bool) -> None:
    if minimal:
        manifest = {"version": 1, "hooks": []}
    else:
        manifest = {
            "version": 1,
            "hooks": [
                {
                    "id": "sample-pre-add",
                    "event": "task.pre_add",
                    "command": ["python", "sample_pre_add.py"],
                },
                {
                    "id": "sample-post-add",
                    "event": "task.post_add",
                    "command": ["python", "sample_post_add.py"],
                    "continue_on_error": True,
                },
            ],
        }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_script(path: Path, template_name: str) -> None:
    content = _read_template(template_name)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _read_template(template_name: str) -> str:
    template_resource = resources.files(HOOK_TEMPLATE_PACKAGE).joinpath(template_name)
    try:
        content = template_resource.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(template_name) from exc
    return content.rstrip("\n") + "\n"


def _progress_label(progress: tuple[int, int] | None) -> str:
    if progress is None:
        return "-"
    remaining, total = progress
    completed = total - remaining
    return f"{completed}/{total}"


def _print_config(config, context: CLIContext) -> None:
    payload = config.model_dump(mode="json")
    context.console.print(json.dumps(payload, indent=2))


def _parse_config_updates(values: list[str] | None) -> dict[str, str]:
    updates: dict[str, str] = {}
    if not values:
        return updates
    for raw in values:
        if "=" not in raw:
            raise typer.BadParameter("Use KEY=VALUE syntax for --set.", param_hint="--set")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise typer.BadParameter("Config key cannot be empty.", param_hint="--set")
        updates[key] = value.strip()
    return updates


def _prepare_config_updates(
    *,
    config: ProjectConfig,
    updates: dict[str, str],
    force: bool,
    console: Console,
) -> dict[str, str]:
    prepared = dict(updates)
    desired_tasks_file = prepared.get("tasks_file")
    if desired_tasks_file is None:
        return prepared
    current_tasks_file = str(config.tasks_file)
    if desired_tasks_file == current_tasks_file:
        prepared.pop("tasks_file", None)
        return prepared
    if force:
        return prepared
    confirmed = typer.confirm(
        f"Change tasks_file from '{current_tasks_file}' "
        f"to '{desired_tasks_file}'? Existing tasks will be migrated to the new storage file.",
        default=False,
    )
    if confirmed:
        return prepared
    console.print("[yellow]Aborted.[/yellow]")
    raise typer.Exit()
