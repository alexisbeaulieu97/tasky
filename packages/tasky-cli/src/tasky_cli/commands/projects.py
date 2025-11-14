"""Commands related to project management in Tasky CLI."""

import tomllib
from pathlib import Path
from typing import Any

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
def init_command(  # noqa: C901
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

    # Import ProjectConfig to use proper schema
    from tasky_projects import ProjectConfig, StorageConfig  # noqa: PLC0415

    # Load existing config or create new one
    if config_file.exists():
        try:
            config = ProjectConfig.from_file(config_file)
            # Update backend while preserving other settings
            config.storage.backend = backend
        except Exception:  # noqa: BLE001
            # If loading fails, create fresh config
            config = ProjectConfig(storage=StorageConfig(backend=backend))
    else:
        # Create new config with proper schema
        config = ProjectConfig(storage=StorageConfig(backend=backend))

    # Save configuration using ProjectConfig (ensures version, created_at, etc.)
    config.to_file(config_file)

    typer.echo(f"✓ Project initialized in {storage_root}")
    typer.echo(f"  Backend: {config.storage.backend}")
    typer.echo(f"  Storage: {config.storage.path}")


@project_app.command(name="info")
def info_command() -> None:
    """Display project configuration information."""
    tasky_dir = Path(".tasky")
    config_toml = tasky_dir / "config.toml"
    config_json = tasky_dir / "config.json"

    # Check for either TOML or JSON config
    if not config_toml.exists() and not config_json.exists():
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
    typer.echo(f"  Location: {tasky_dir.absolute()}")
    typer.echo(f"  Backend: {settings.storage.backend}")
    typer.echo(f"  Storage: {settings.storage.path}")


@project_app.command(name="list")
def list_command(
    recursive: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--recursive",
        "-r",
        help="Search recursively in all subdirectories",
    ),
    root: Path | None = typer.Option(  # noqa: B008
        None,
        "--root",
        help="Root directory to search from (default: current directory)",
    ),
) -> None:
    """List all tasky projects.

    By default, searches upward from current directory to find parent projects.
    Use --recursive to search all subdirectories instead.
    Use --root to specify a different starting directory.

    """
    from tasky_projects import find_projects_recursive, find_projects_upward  # noqa: PLC0415

    # Determine search directory
    search_dir = root if root else Path.cwd()

    # Find projects based on flags
    if recursive:
        projects = find_projects_recursive(search_dir)
    else:
        projects = find_projects_upward(search_dir)

    # Handle empty results
    if not projects:
        typer.echo("No projects found.")
        typer.echo("Run 'tasky project init' to create one.")
        return

    # Display results
    count = len(projects)
    plural = "project" if count == 1 else "projects"
    typer.echo(f"Found {count} {plural}:\n")

    for project in projects:
        typer.echo(f"  Path:    {project.path}")
        typer.echo(f"  Backend: {project.backend}")
        typer.echo(f"  Storage: {project.storage_path}")
        typer.echo()  # Blank line between projects
