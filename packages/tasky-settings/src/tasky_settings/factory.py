"""Service factory for creating configured task services."""

from __future__ import annotations

import threading
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

from tasky_tasks.service import TaskService

from tasky_settings.backend_registry import registry
from tasky_settings.configuration import get_settings

if TYPE_CHECKING:
    from tasky_hooks.dispatcher import HookDispatcher

# Backend initialization state (thread-safe)
# Using a list to avoid global statement - mutable container can be modified
_backends_initialized = [False]
_init_lock = threading.Lock()


def _ensure_backends_registered() -> None:
    """Ensure storage backends are registered before using the registry.

    This function imports tasky_storage, which triggers backend self-registration
    via module-level code. It runs once on first call to create_task_service().

    Thread-safe: Uses a lock to ensure single initialization even in multi-threaded
    environments (e.g., MCP servers).

    Backend Registration Pattern
    ============================

    This implements an intentional self-registration pattern:

    1. Each backend registers itself at import time by calling:
           from tasky_settings import registry
           registry.register("backend-name", factory_function)

    2. tasky_settings.factory._ensure_backends_registered() triggers import of
       tasky_storage, which causes all backends to register

    3. This design choice enables:
       - tasky_settings remains generic (no backend-specific knowledge)
       - New backends added without modifying settings
       - Third-party backends can self-register by following the pattern
       - Service factory works without requiring explicit tasky_storage import
       - Tests can use the factory in isolation

    Why not explicit registration in settings?
    - Would couple settings to every backend
    - Would require settings changes for each new backend (SQLite, PostgreSQL, etc.)
    - Would break third-party backend extensibility
    - Settings should remain a configuration/wiring layer, not a coupling point

    See: docs/architecture.md#backend-registration-pattern for full details

    """
    with _init_lock:
        if not _backends_initialized[0]:
            # Import triggers backend registration via tasky_storage.__init__.py
            import_module("tasky_storage")

            _backends_initialized[0] = True


class ProjectNotFoundError(Exception):
    """Raised when no project configuration is found."""

    def __init__(self, start_path: Path) -> None:
        """Initialize the exception.

        Args:
            start_path: The path where the search started

        """
        super().__init__(
            f"No project found. Searched from {start_path} up to root. "
            "Run 'tasky project init' to create a project.",
        )
        self.start_path = start_path


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the project root by searching for .tasky directory.

    Walks up the directory tree from start_path until it finds a directory
    containing a .tasky subdirectory (which indicates a project).

    Args:
        start_path: Starting path for the search. Defaults to current directory.

    Returns:
        Path to the project root (parent of .tasky directory)

    Raises:
        ProjectNotFoundError: If no project directory is found

    """
    current = start_path or Path.cwd()
    current = current.resolve()

    # Search current directory and all parents
    for path in [current, *current.parents]:
        tasky_dir = path / ".tasky"
        if tasky_dir.is_dir():
            return path

    raise ProjectNotFoundError(current)


def create_task_service(
    project_root: Path | None = None,
    dispatcher: HookDispatcher | None = None,
) -> TaskService:
    """Create a TaskService instance from project configuration.

    This factory function:
    1. Ensures storage backends are initialized (auto-imports tasky_storage)
    2. Finds the project root (if not provided)
    3. Loads the settings from .tasky/config.toml
    4. Gets the appropriate backend factory from the registry
    5. Creates and initializes the repository
    6. Returns a configured TaskService

    Args:
        project_root: Path to project root. If None, searches from current directory.
        dispatcher: Optional hook dispatcher for event handling.

    Returns:
        Configured TaskService instance

    Raises:
        ProjectNotFoundError: If no project directory is found

    """
    # Ensure backends are available before accessing registry
    _ensure_backends_registered()

    # Find project root if not provided
    if project_root is None:
        project_root = find_project_root()
    else:
        # If project_root is provided, verify it exists
        project_root = project_root.resolve()
        tasky_dir = project_root / ".tasky"
        if not tasky_dir.is_dir():
            raise ProjectNotFoundError(project_root)

    # Load settings with project root context
    settings = get_settings(project_root=project_root)

    # Get backend factory
    factory = registry.get(settings.storage.backend)

    # Construct absolute storage path
    storage_path = project_root / ".tasky" / settings.storage.path

    # Create repository
    repository = factory(storage_path)

    # Initialize storage
    repository.initialize()

    # Return configured service
    return TaskService(
        repository=repository,
        dispatcher=dispatcher,
        project_root=str(project_root),
    )
