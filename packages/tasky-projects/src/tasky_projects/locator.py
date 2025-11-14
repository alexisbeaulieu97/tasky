"""Project discovery and location utilities."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from tasky_projects.config import ProjectConfig

logger = logging.getLogger(__name__)


@dataclass
class ProjectLocation:
    """Information about a discovered project.

    Attributes:
        path: Absolute path to the project directory (containing .tasky/)
        backend: Storage backend configured for the project
        storage_path: Path to the storage file relative to .tasky/

    """

    path: Path
    backend: str
    storage_path: str

    def __post_init__(self) -> None:
        """Ensure path is always absolute."""
        self.path = self.path.resolve()

    def __lt__(self, other: ProjectLocation) -> bool:
        """Compare by path for sorting."""
        return str(self.path) < str(other.path)


def _load_project_config(config_path: Path) -> dict[str, str] | None:
    """Load project configuration file.

    Args:
        config_path: Path to .tasky/config.toml file

    Returns:
        Dictionary with 'backend' and 'storage_path' keys, or None if loading fails

    """
    try:
        config = ProjectConfig.from_file(config_path)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to load config from %s: %s", config_path, exc)
        return None
    else:
        return {"backend": config.storage.backend, "storage_path": config.storage.path}


def _check_directory_for_project(directory: Path) -> ProjectLocation | None:
    """Check if a directory contains a tasky project.

    Args:
        directory: Directory to check for .tasky/config.toml

    Returns:
        ProjectLocation if found, None otherwise

    """
    tasky_dir = directory / ".tasky"
    config_path = tasky_dir / "config.toml"

    if not config_path.exists():
        config_path = tasky_dir / "config.json"

    if not config_path.exists():
        return None

    config_data = _load_project_config(config_path)
    if not config_data:
        return None

    return ProjectLocation(
        path=directory,
        backend=config_data["backend"],
        storage_path=config_data["storage_path"],
    )


def find_projects_upward(start_dir: Path | None = None) -> list[ProjectLocation]:
    """Find all tasky projects from start_dir upward to filesystem root.

    Searches from start_dir upward through parent directories until reaching
    the filesystem root or home directory. Stops at home directory to avoid
    searching system directories.

    Args:
        start_dir: Starting directory for search (default: current directory)

    Returns:
        List of ProjectLocation objects sorted by path

    """
    start_dir = Path.cwd() if start_dir is None else start_dir.resolve()

    projects: list[ProjectLocation] = []
    home_dir = Path.home()
    current = start_dir

    # Walk upward until we hit root or home
    while True:
        project = _check_directory_for_project(current)
        if project:
            projects.append(project)

        # Stop at filesystem root or home directory
        parent = current.parent
        if current in (parent, home_dir):
            break
        current = parent

    return sorted(projects)


def find_projects_recursive(root_dir: Path | None = None) -> list[ProjectLocation]:
    """Find all tasky projects recursively under root_dir.

    Traverses the entire directory tree under root_dir searching for .tasky
    directories. Handles permission errors gracefully by skipping inaccessible
    directories.

    Args:
        root_dir: Root directory to search from (default: current directory)

    Returns:
        List of ProjectLocation objects sorted by path

    """
    root_dir = Path.cwd() if root_dir is None else root_dir.resolve()
    projects: list[ProjectLocation] = []

    def handle_error(err: OSError) -> None:
        """Handle permission errors by logging and continuing."""
        logger.debug("Skipping directory due to error: %s", err)

    for dirpath, dirnames, _filenames in os.walk(root_dir, onerror=handle_error):
        current_path = Path(dirpath)
        project = _check_directory_for_project(current_path)

        if project:
            projects.append(project)
            # Don't descend into .tasky directories
            if ".tasky" in dirnames:
                dirnames.remove(".tasky")

    return sorted(projects)
