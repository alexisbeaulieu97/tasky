"""Commands related to project management in Tasky CLI."""

from pathlib import Path

import typer
from tasky_settings import get_project_registry_service, get_settings, registry

project_app = typer.Typer(no_args_is_help=True)


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
def info_command(  # noqa: C901
    project_name: str | None = typer.Option(
        None,
        "--project-name",
        "-p",
        help="Name of registered project to show info for",
    ),
) -> None:
    """Display project configuration information.

    If no project name is provided, shows info for the current directory.
    If a project name is provided, looks it up in the global registry.

    """
    if project_name:
        # Look up project in registry
        try:
            registry_service = get_project_registry_service()
            project = registry_service.get_project(project_name)
            if project is None:
                typer.echo(f"Error: Project '{project_name}' not found in registry.", err=True)
                typer.echo("Run 'tasky project list' to see all registered projects.", err=True)
                raise typer.Exit(code=1)  # noqa: TRY301

            # Display registry project information
            typer.echo(f"Project: {project.name}")
            typer.echo(f"  Path: {project.path}")
            typer.echo(f"  Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
            typer.echo(f"  Last accessed: {project.last_accessed.strftime('%Y-%m-%d %H:%M')}")
            if project.tags:
                typer.echo(f"  Tags: {', '.join(project.tags)}")

            # Check if path still exists
            if not project.path.exists():
                typer.echo("  Status: [MISSING]", err=True)
        except Exception as exc:
            typer.echo(f"Error accessing registry: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        # Show info for current directory
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
def list_command(  # noqa: C901
    no_discover: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--no-discover",
        help="Skip auto-discovery of projects",
    ),
) -> None:
    """List all registered tasky projects.

    On first use, automatically discovers and registers projects in common directories.
    Use --no-discover to skip automatic discovery.

    """
    try:
        registry_service = get_project_registry_service()
        settings = get_settings()

        # Auto-discover on first use (if registry is empty and not skipped)
        projects = registry_service.list_projects()
        if not projects and not no_discover:
            typer.echo("Discovering projects...")
            new_count = registry_service.discover_and_register(
                settings.project_registry.discovery_paths,
            )
            if new_count > 0:
                typer.echo(f"✓ Discovered and registered {new_count} project(s)\n")
                projects = registry_service.list_projects()

        # Handle empty results
        if not projects:
            typer.echo("No projects found.")
            typer.echo("Run 'tasky project init' to create one, or")
            typer.echo("'tasky project discover' to search for existing projects.")
            return

        # Display results
        count = len(projects)
        plural = "project" if count == 1 else "projects"
        typer.echo(f"Found {count} registered {plural}:\n")

        for project in projects:
            # Check if path still exists
            status = "" if project.path.exists() else " [MISSING]"
            typer.echo(f"  {project.name}{status}")
            typer.echo(f"    Path: {project.path}")
            typer.echo(f"    Last accessed: {project.last_accessed.strftime('%Y-%m-%d %H:%M')}")
            typer.echo()  # Blank line between projects

    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@project_app.command(name="register")
def register_command(
    path: str = typer.Argument(..., help="Path to the project directory"),
) -> None:
    """Register a project in the global registry.

    The path must be a directory containing a .tasky subdirectory.

    """
    try:
        # Resolve path to absolute
        resolved_path = Path(path).resolve()

        # Validate path exists
        if not resolved_path.exists():
            typer.echo(f"Error: Path does not exist: {resolved_path}", err=True)
            raise typer.Exit(code=1)  # noqa: TRY301

        if not resolved_path.is_dir():
            typer.echo(f"Error: Path is not a directory: {resolved_path}", err=True)
            raise typer.Exit(code=1)  # noqa: TRY301

        # Register the project
        registry_service = get_project_registry_service()
        project = registry_service.register_project(resolved_path)

        typer.echo(f"✓ Project registered: {project.name}")
        typer.echo(f"  Path: {project.path}")

    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@project_app.command(name="unregister")
def unregister_command(  # noqa: C901
    name: str = typer.Argument(..., help="Name of the project to unregister"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),  # noqa: FBT001, FBT003
) -> None:
    """Remove a project from the global registry.

    This only removes the project from the registry; it does not delete any files.

    """
    try:
        registry_service = get_project_registry_service()

        # Get project to confirm it exists
        project = registry_service.get_project(name)
        if not project:
            typer.echo(f"Error: Project '{name}' not found in registry.", err=True)
            typer.echo("Run 'tasky project list' to see all registered projects.", err=True)
            raise typer.Exit(code=1)  # noqa: TRY301

        # Confirm deletion
        if not yes:
            typer.echo(f"Project: {name}")
            typer.echo(f"  Path: {project.path}")
            confirm = typer.confirm("\nAre you sure you want to unregister this project?")
            if not confirm:
                typer.echo("Cancelled.")
                raise typer.Exit(code=0)  # noqa: TRY301

        # Unregister the project
        registry_service.unregister_project(project.path)
        typer.echo(f"✓ Project unregistered: {name}")

    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@project_app.command(name="discover")
def discover_command(  # noqa: C901
    paths: list[Path] | None = typer.Option(  # noqa: B008
        None,
        "--path",
        "-p",
        help="Custom path to search (can be specified multiple times)",
    ),
) -> None:
    """Discover and register tasky projects.

    Searches common directories for .tasky projects and registers them.
    Use --path to specify custom search directories.

    """
    try:
        registry_service = get_project_registry_service()
        settings = get_settings()

        # Use custom paths if provided, otherwise use defaults from settings
        search_paths = paths if paths else settings.project_registry.discovery_paths

        typer.echo("Discovering projects...")
        typer.echo("Searching in:")
        for path in search_paths:
            typer.echo(f"  - {path}")
        typer.echo()

        # Discover and register
        new_count = registry_service.discover_and_register(search_paths)

        if new_count > 0:
            typer.echo(f"✓ Discovered and registered {new_count} new project(s)")
            # Show newly registered projects
            projects = registry_service.list_projects()
            typer.echo("\nAll registered projects:")
            for project in projects:
                typer.echo(f"  - {project.name} ({project.path})")
        else:
            typer.echo("No new projects found.")
            total = len(registry_service.list_projects())
            if total > 0:
                typer.echo(f"(Already tracking {total} project(s))")

    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
