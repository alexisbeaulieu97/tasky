"""Commands related to project management in Tasky CLI."""

from pathlib import Path

import typer
from tasky_storage.backends.json.repository import JsonTaskRepository
from tasky_storage.backends.json.storage import JsonStorage

project_app = typer.Typer(no_args_is_help=True)


@project_app.command(name="init")
def init_command() -> None:
    """Initialize a new project."""
    typer.echo("Initializing project...")

    storage_root = Path(".tasky")
    storage_root.mkdir(parents=True, exist_ok=True)

    storage_file = storage_root / "tasks.json"
    storage = JsonStorage(path=storage_file)

    repository = JsonTaskRepository(storage=storage)
    repository.initialize()

    typer.echo(f"Project initialized in {storage_root} (storage: {storage_file.name})")


@project_app.command(name="list")
def list_command() -> None:
    """List all projects."""
    typer.echo("Listing projects...")
