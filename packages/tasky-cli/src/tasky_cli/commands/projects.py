"""Commands related to project management in Tasky CLI."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from tasky_projects import ProjectConfig, StorageConfig
from tasky_projects.models import ProjectMetadata
from tasky_projects.registry import ProjectRegistryService
from tasky_settings import get_project_registry_service, get_settings, registry

project_app = typer.Typer(no_args_is_help=True)


@project_app.command(name="init")
def init_command(
    backend: str = typer.Option("json", "--backend", "-b", help="Storage backend to use"),
) -> None:
    """Initialize a Tasky project with the selected storage backend.

    Parameters
    ----------
    backend:
        Name of the registered storage backend to use for the project.

    Returns
    -------
    None

    Notes
    -----
    Equivalent to running ``tasky project init --backend <name>`` from the CLI.
    """

    storage_root = Path(".tasky")
    config_file = storage_root / "config.toml"

    with _cli_error_boundary("while initializing project"):
        _validate_backend_selection(backend)
        _ensure_overwrite_allowed(config_file)
        config = _load_or_create_project_config(config_file, backend)
        config.to_file(config_file)
        _echo_init_success(config, storage_root)


@project_app.command(name="info")
def info_command(
    project_name: str | None = typer.Option(
        None,
        "--project-name",
        "-p",
        help="Name of registered project to show info for",
    ),
) -> None:
    """Display project configuration information.

    Parameters
    ----------
    project_name:
        Optional project registered in the global registry. When omitted the
        command inspects the current directory.

    Returns
    -------
    None

    Notes
    -----
    Useful when switching between multiple Tasky projects and verifying
    registry entries.
    """

    with _cli_error_boundary("while displaying project info"):
        if project_name:
            _show_registry_project_info(project_name)
            return
        _show_current_directory_info()


def _format_project_path(project_path: Path) -> str:
    """Format project path with tilde shortening for home directory.

    Args:
        project_path: The path to format

    Returns:
        Formatted path string with ~ for home directory

    """
    try:
        if project_path.is_relative_to(Path.home()):
            return str(project_path).replace(str(Path.home()), "~")
        return str(project_path)
    except (ValueError, OSError):
        return str(project_path)


def _format_project_line(
    project: ProjectMetadata,
    max_name_width: int = 20,
    max_path_width: int = 30,
) -> str:
    """Format a single project entry for display.

    Args:
        project: The project metadata to format
        max_name_width: Maximum width for project name
        max_path_width: Maximum width for path display

    Returns:
        Formatted line string

    """
    status = "" if project.path.exists() else " [MISSING]"
    path_display = _format_project_path(project.path)
    last_accessed_str = project.last_accessed.strftime("%Y-%m-%d %H:%M")

    # Truncate name and path if too long
    name_display = (
        project.name
        if len(project.name) <= max_name_width
        else f"{project.name[: max_name_width - 1]}…"
    )
    path_truncated = (
        path_display
        if len(path_display) <= max_path_width
        else f"{path_display[: max_path_width - 1]}…"
    )

    return f"  {name_display:<20} {path_truncated:<30} Last accessed: {last_accessed_str}{status}"


def _clean_stale_projects(
    registry_service: ProjectRegistryService,
    stale_projects: list[ProjectMetadata],
) -> None:
    """Remove stale projects from registry and display results.

    Args:
        registry_service: The registry service to use
        stale_projects: List of projects with missing paths

    """
    typer.echo(f"Removing {len(stale_projects)} stale project(s)...")
    for project in stale_projects:
        try:
            registry_service.unregister_project(project.path)
            typer.echo(f"  ✓ Removed: {project.name}")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"  ✗ Failed to remove {project.name}: {exc}", err=True)


def _display_projects(projects: list[ProjectMetadata]) -> None:
    """Display list of projects in formatted table.

    Args:
        projects: List of projects to display

    """
    typer.echo("Projects:")
    for project in projects:
        typer.echo(_format_project_line(project))


def _auto_discover_if_empty(
    registry_service: ProjectRegistryService,
    projects: list[ProjectMetadata],
    discovery_paths: list[Path],
    skip_discovery: bool,  # noqa: FBT001
) -> list[ProjectMetadata]:
    """Auto-discover projects if registry is empty and discovery not skipped.

    Args:
        registry_service: The registry service to use
        projects: Current list of projects
        discovery_paths: Paths to search for projects
        skip_discovery: Whether to skip auto-discovery

    Returns:
        Updated list of projects after discovery

    """
    if not projects and not skip_discovery:
        typer.echo("Discovering projects...")
        new_count = registry_service.discover_and_register(discovery_paths)
        if new_count > 0:
            typer.echo(f"✓ Discovered and registered {new_count} project(s)\n")
            return registry_service.list_projects()
    return projects


def _show_stale_summary(
    stale_projects: list[ProjectMetadata],
    cleaned: bool,  # noqa: FBT001
    validate_mode: bool,  # noqa: FBT001
) -> None:
    """Display summary of stale project entries.

    Args:
        stale_projects: List of projects with missing paths
        cleaned: Whether stale projects were cleaned
        validate_mode: Whether in validation mode

    """
    if not stale_projects:
        if validate_mode:
            typer.echo("")
            typer.echo("✓ All project paths are valid")
        return

    typer.echo("")
    if cleaned:
        return
    if validate_mode:
        typer.echo(f"✗ {len(stale_projects)} project(s) have missing paths")
    else:
        typer.echo(f"Note: {len(stale_projects)} project(s) have missing paths.")
        typer.echo(
            "Use 'tasky project list --clean' to remove them from the registry.",
        )


@contextmanager
def _cli_error_boundary(action: str) -> Iterator[None]:
    """Provide consistent CLI error handling for project commands.

    Parameters
    ----------
    action:
        Human-readable phrase used when describing the failure.

    Yields
    ------
    Iterator[None]
        Context manager sentinel for the protected block.

    """

    try:
        yield
    except typer.Exit:
        raise
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        if action:
            typer.echo(f"(while {action})", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Unexpected error {action}: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _validate_backend_selection(backend: str) -> None:
    """Ensure the provided backend is registered.

    Parameters
    ----------
    backend:
        Backend identifier supplied via CLI options.

    Raises
    ------
    ValueError
        If the backend is not registered in the settings registry.

    """

    try:
        registry.get(backend)
    except KeyError as exc:  # noqa: B904
        available = ", ".join(sorted(registry.list_backends()))
        msg = f"Backend '{backend}' not registered. Available backends: {available}"
        raise ValueError(msg) from exc


def _ensure_overwrite_allowed(config_file: Path) -> None:
    """Confirm overwriting an existing config file when necessary.

    Parameters
    ----------
    config_file:
        Full path to the configuration file that may be overwritten.

    Returns
    -------
    None
        Raises ``typer.Exit`` if the user declines overwriting.
    """

    if not config_file.exists():
        return

    typer.echo(f"Warning: Project already exists in {config_file.parent}", err=True)
    if not typer.confirm("Overwrite existing configuration?"):
        raise typer.Exit(code=0)


def _load_or_create_project_config(config_file: Path, backend: str) -> ProjectConfig:
    """Load an existing project config or create a new one.

    Parameters
    ----------
    config_file:
        Path to the TOML configuration file.
    backend:
        Backend that should be written into the config.

    Returns
    -------
    ProjectConfig
        Validated configuration ready to be persisted.
    """

    if config_file.exists():
        try:
            config = ProjectConfig.from_file(config_file)
            config.storage.backend = backend
            return config
        except Exception:  # noqa: BLE001
            return ProjectConfig(storage=StorageConfig(backend=backend))
    return ProjectConfig(storage=StorageConfig(backend=backend))


def _echo_init_success(config: ProjectConfig, storage_root: Path) -> None:
    """Display a success summary after writing configuration.

    Parameters
    ----------
    config:
        Persisted configuration instance.
    storage_root:
        Directory where Tasky metadata is stored.

    Returns
    -------
    None
        Writes formatted status messages to stdout.
    """

    typer.echo(f"✓ Project initialized in {storage_root}")
    typer.echo(f"  Backend: {config.storage.backend}")
    typer.echo(f"  Storage: {config.storage.path}")


def _show_registry_project_info(project_name: str) -> None:
    """Display registry-maintained project details.

    Parameters
    ----------
    project_name:
        Name of the project stored in the global registry.

    Returns
    -------
    None
        Raises ``ValueError`` when the project does not exist.
    """

    registry_service = get_project_registry_service()
    project = registry_service.get_project(project_name)
    if project is None:
        msg = f"Project '{project_name}' not found in registry."
        raise ValueError(msg)

    typer.echo(f"Project: {project.name}")
    typer.echo(f"  Path: {project.path}")
    typer.echo(f"  Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
    typer.echo(f"  Last accessed: {project.last_accessed.strftime('%Y-%m-%d %H:%M')}")
    if project.tags:
        typer.echo(f"  Tags: {', '.join(project.tags)}")
    if not project.path.exists():
        typer.echo("  Status: [MISSING]", err=True)


def _show_current_directory_info() -> None:
    """Display configuration details for the current directory.

    Returns
    -------
    None
        Raises ``ValueError`` if the directory is not a Tasky project.
    """

    tasky_dir = Path(".tasky")
    config_toml = tasky_dir / "config.toml"
    if not config_toml.exists():
        msg = "No project found in current directory. Run 'tasky project init' to create one."
        raise ValueError(msg)

    settings = get_settings()
    project_root = tasky_dir.parent.resolve()
    typer.echo("Project Information:")
    typer.echo(f"  Location: {project_root}")
    typer.echo(f"  Backend: {settings.storage.backend}")
    typer.echo(f"  Storage: {settings.storage.path}")


def _validate_project_directory(path: str) -> Path:
    """Validate that ``path`` points to an existing Tasky project.

    Parameters
    ----------
    path:
        User-provided filesystem path.

    Returns
    -------
    Path
        Resolved absolute path to the Tasky project.

    Raises
    ------
    ValueError
        If the path cannot be used as a Tasky project.
    """

    resolved_path = Path(path).resolve()
    if not resolved_path.exists():
        msg = f"Path does not exist: {resolved_path}"
        raise ValueError(msg)
    if not resolved_path.is_dir():
        msg = f"Path is not a directory: {resolved_path}"
        raise ValueError(msg)
    if not (resolved_path / ".tasky").is_dir():
        msg = f"Not a Tasky project (missing .tasky directory): {resolved_path}"
        raise ValueError(msg)
    return resolved_path


def _confirm_unregister(project: ProjectMetadata, skip_confirmation: bool) -> None:
    """Prompt before unregistering unless ``skip_confirmation`` is True.

    Parameters
    ----------
    project:
        Registry entry that may be removed.
    skip_confirmation:
        Whether to bypass the confirmation prompt.

    Returns
    -------
    None
        Raises ``typer.Exit`` if the user cancels the operation.
    """

    if skip_confirmation:
        return

    typer.echo(f"Project: {project.name}")
    typer.echo(f"  Path: {project.path}")
    confirm = typer.confirm("\nAre you sure you want to unregister this project?")
    if not confirm:
        typer.echo("Cancelled.")
        raise typer.Exit(code=0)


def _resolve_discovery_paths(paths: list[Path] | None) -> list[Path]:
    """Return the search paths for discovery, resolving defaults if needed.

    Parameters
    ----------
    paths:
        Optional custom paths provided through CLI options.

    Returns
    -------
    list[Path]
        List of paths that should be scanned for Tasky projects.
    """

    if paths:
        return [path.resolve() for path in paths]
    settings = get_settings()
    return settings.project_registry.discovery_paths


def _run_discovery_flow(
    registry_service: ProjectRegistryService,
    search_paths: list[Path],
) -> None:
    """Execute discovery flow with progress feedback.

    Parameters
    ----------
    registry_service:
        Service used to discover and record projects.
    search_paths:
        Paths that should be scanned for Tasky metadata.

    Returns
    -------
    None
        Prints progress and discovery summaries to stdout.
    """

    typer.echo("Discovering projects...")
    typer.echo("Searching in:")
    for path in search_paths:
        typer.echo(f"  - {path}")
    typer.echo()

    def show_progress(directories_checked: int) -> None:
        typer.echo(f"\rScanning... ({directories_checked} directories checked)", nl=False)

    new_count = registry_service.discover_and_register(
        search_paths,
        progress_callback=show_progress,
    )
    typer.echo()

    if new_count > 0:
        typer.echo(f"✓ Discovered and registered {new_count} new project(s)")
        projects = registry_service.list_projects()
        typer.echo("\nAll registered projects:")
        for project in projects:
            typer.echo(f"  - {project.name} ({project.path})")
        return

    typer.echo("No new projects found.")
    total = len(registry_service.list_projects())
    if total > 0:
        typer.echo(f"(Already tracking {total} project(s))")


@project_app.command(name="list")
def list_command(
    no_discover: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--no-discover",
        help="Skip auto-discovery of projects",
    ),
    validate: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--validate",
        help="Check if all registered project paths still exist",
    ),
    clean: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--clean",
        help="Remove projects with missing paths from registry",
    ),
) -> None:
    """List all registered Tasky projects.

    Parameters
    ----------
    no_discover:
        When ``True`` the command skips discovery even if the registry is empty.
    validate:
        Emit a summary of invalid paths instead of silently ignoring them.
    clean:
        Remove any stale projects whose paths are missing from disk.

    Returns
    -------
    None

    Notes
    -----
    Automatically triggers discovery the first time you run ``tasky project list``.
    """
    try:
        registry_service = get_project_registry_service()
        settings = get_settings()

        # Auto-discover on first use
        projects = registry_service.list_projects()
        projects = _auto_discover_if_empty(
            registry_service,
            projects,
            settings.project_registry.discovery_paths,
            no_discover,
        )

        # Handle empty results
        if not projects:
            typer.echo("No projects found.")
            typer.echo("Run 'tasky project init' to create one, or")
            typer.echo("'tasky project discover' to search for existing projects.")
            return

        # Find and optionally clean stale entries
        stale_projects = [p for p in projects if not p.path.exists()]
        if clean and stale_projects:
            _clean_stale_projects(registry_service, stale_projects)
            projects = [p for p in projects if p.path.exists()]

        # Display results and summary
        _display_projects(projects)
        _show_stale_summary(stale_projects, clean, validate)

    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@project_app.command(name="register")
def register_command(
    path: str = typer.Argument(..., help="Path to the project directory"),
) -> None:
    """Register an existing project path in the global registry.

    Parameters
    ----------
    path:
        Filesystem path that points to a directory containing a ``.tasky`` folder.

    Returns
    -------
    None

    Notes
    -----
    Lets shared workstations register existing repositories without running
    ``tasky project init`` again.
    """

    with _cli_error_boundary("while registering project"):
        resolved_path = _validate_project_directory(path)
        registry_service = get_project_registry_service()
        project = registry_service.register_project(resolved_path)
        typer.echo(f"✓ Project registered: {project.name}")
        typer.echo(f"  Path: {project.path}")


@project_app.command(name="unregister")
def unregister_command(
    name: str = typer.Argument(..., help="Name of the project to unregister"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),  # noqa: FBT001, FBT003
) -> None:
    """Remove a project entry from the registry without touching files.

    Parameters
    ----------
    name:
        Registered project name to remove from the global registry.
    yes:
        When ``True`` the confirmation prompt is skipped.

    Returns
    -------
    None

    Notes
    -----
    Use together with ``tasky project list --clean`` to prune stale entries.
    """

    with _cli_error_boundary("while unregistering project"):
        registry_service = get_project_registry_service()
        project = registry_service.get_project(name)
        if project is None:
            typer.echo("Run 'tasky project list' to view registered projects.", err=True)
            raise ValueError(f"Project not found: {name}")

        _confirm_unregister(project, yes)
        registry_service.unregister_project(project.path)
        typer.echo(f"✓ Project unregistered: {name}")


@project_app.command(name="discover")
def discover_command(
    paths: list[Path] | None = typer.Option(  # noqa: B008
        None,
        "--path",
        "-p",
        help="Custom path to search (can be specified multiple times)",
    ),
) -> None:
    """Discover and register projects under well-known directories.

    Parameters
    ----------
    paths:
        Optional custom directories to search. Defaults to the configured
        discovery paths when omitted.

    Returns
    -------
    None

    Notes
    -----
    Shows a live progress indicator while scanning directories.
    """

    with _cli_error_boundary("while discovering projects"):
        registry_service = get_project_registry_service()
        search_paths = _resolve_discovery_paths(paths)
        _run_discovery_flow(registry_service, search_paths)
