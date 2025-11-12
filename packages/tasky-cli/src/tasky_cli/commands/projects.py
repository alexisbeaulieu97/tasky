"""Commands related to project management in Tasky CLI."""

import tomllib
from pathlib import Path
from typing import Any, cast

import typer
from tasky_settings import get_settings, registry

project_app = typer.Typer(no_args_is_help=True)


def _load_toml_file(path: Path) -> dict[str, Any]:
    """Load a TOML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _save_toml_file(path: Path, data: dict[str, Any]) -> None:
    """Save data to a TOML file using tomli_w."""
    try:
        import tomli_w  # noqa: PLC0415
    except ImportError as e:
        typer.echo(
            "Error: tomli_w package required for TOML writing. Install with: pip install tomli_w",
            err=True,
        )
        raise typer.Exit(code=1) from e

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)


@project_app.command(name="init")
def init_command(
    backend: str = typer.Option("json", "--backend", "-b", help="Storage backend to use"),
) -> None:
    """Initialize a new project."""
    # Validate backend exists
    try:
        registry.get(backend)
    except KeyError:
        available = ", ".join(registry.list_backends())
        typer.echo(f"Error: Backend '{backend}' not registered.", err=True)
        typer.echo(f"Available backends: {available}", err=True)
        raise typer.Exit(code=1) from None

    storage_root = Path(".tasky")
    config_file = storage_root / "config.toml"

    # Check if project already exists
    if config_file.exists():
        typer.echo(f"Warning: Project already exists in {storage_root}", err=True)
        confirm = typer.confirm("Overwrite existing configuration?")
        if not confirm:
            raise typer.Exit(code=0)

    # Load existing config or start fresh
    config_data = _load_toml_file(config_file)

    # Ensure storage section exists and update backend
    if "storage" not in config_data:
        config_data["storage"] = {}
    storage = cast("dict[str, Any]", config_data["storage"])
    storage["backend"] = backend
    storage["path"] = storage.get("path", "tasks.json")

    # Save configuration
    _save_toml_file(config_file, config_data)

    typer.echo(f"✓ Project initialized in {storage_root}")
    typer.echo(f"  Backend: {backend}")
    typer.echo(f"  Storage: {storage['path']}")


@project_app.command(name="info")
def info_command() -> None:
    """Display project configuration information."""
    config_file = Path(".tasky") / "config.toml"

    if not config_file.exists():
        typer.echo("Error: No project found in current directory.", err=True)
        typer.echo("Run 'tasky project init' to create a project.", err=True)
        raise typer.Exit(code=1)

    # Load settings to get validated configuration
    try:
        settings = get_settings()
    except Exception as exc:
        typer.echo(f"Error loading configuration: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # Display project information
    typer.echo("Project Information:")
    typer.echo(f"  Location: {config_file.parent.absolute()}")
    typer.echo(f"  Backend: {settings.storage.backend}")
    typer.echo(f"  Storage: {settings.storage.path}")


@project_app.command(name="list")
def list_command() -> None:
    """List all projects."""
    typer.echo("Listing projects...")
