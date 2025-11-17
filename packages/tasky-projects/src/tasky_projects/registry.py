"""Project registry service for managing and discovering projects."""

import json
import logging
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from tasky_projects.models import ProjectMetadata, ProjectRegistry

logger = logging.getLogger(__name__)

# Maximum number of projects that can be stored in the registry
# This prevents unbounded memory growth when loading the registry
MAX_REGISTRY_SIZE = 10_000

# Warning threshold: warn when registry approaches maximum size
REGISTRY_SIZE_WARNING_THRESHOLD = 0.9  # 90% of max size

# Maximum number of attempts to disambiguate project names
# Prevents infinite loops when trying to resolve name collisions
MAX_DISAMBIGUATION_ATTEMPTS = 100


def _validate_project_path(path: Path) -> Path:
    """Validate that path exists and contains .tasky directory.

    Args:
        path: Path to validate

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path doesn't exist or lacks .tasky directory

    """
    path = path.resolve()
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise ValueError(msg)

    tasky_dir = path / ".tasky"
    if not tasky_dir.exists() or not tasky_dir.is_dir():
        msg = "Not a tasky project (missing .tasky directory)"
        raise ValueError(msg)

    return path


def _check_registry_size_limits(current_size: int) -> None:
    """Check registry size against hard and warning limits.

    Args:
        current_size: Current number of projects in registry

    Raises:
        ValueError: If hard limit is exceeded

    """
    if current_size >= MAX_REGISTRY_SIZE:
        msg = (
            f"Registry size limit exceeded ({current_size}/{MAX_REGISTRY_SIZE}). "
            "Consider removing unused projects or increasing the limit."
        )
        raise ValueError(msg)

    warning_threshold = int(MAX_REGISTRY_SIZE * REGISTRY_SIZE_WARNING_THRESHOLD)
    if current_size >= warning_threshold:
        logger.warning(
            "Registry approaching size limit: %d/%d projects registered",
            current_size,
            MAX_REGISTRY_SIZE,
        )


def _disambiguate_with_parent(
    path: Path,
    base_name: str,
    registry: ProjectRegistry,
) -> str:
    """Try to disambiguate name using parent directory name.

    Args:
        path: Project path
        base_name: Base name to disambiguate
        registry: Registry to check for collisions

    Returns:
        Disambiguated name

    Raises:
        ValueError: If disambiguation fails after max attempts

    """
    try:
        parent_name = path.parent.name
        candidate = f"{base_name}-{parent_name}"
        logger.debug("Trying disambiguation with parent name: '%s'", candidate)

        # If still colliding, add numeric suffix
        i = 1
        while registry.get_by_name(candidate):
            existing = registry.get_by_name(candidate)
            if existing and existing.path == path:
                break
            candidate = f"{base_name}-{parent_name}-{i}"
            i += 1
            if i > MAX_DISAMBIGUATION_ATTEMPTS:
                msg = (
                    f"Failed to disambiguate project name "
                    f"after {MAX_DISAMBIGUATION_ATTEMPTS} attempts: {base_name}"
                )
                raise ValueError(msg)
        else:
            logger.info(
                "Successfully disambiguated '%s' to '%s' (strategy: parent-name + suffix)",
                base_name,
                candidate,
            )

        return candidate  # noqa: TRY300

    except (OSError, AttributeError) as exc:
        logger.warning(
            "Cannot use parent directory for disambiguation (%s: %s), using numeric suffix",
            type(exc).__name__,
            exc,
        )
        return _disambiguate_with_numeric_suffix(base_name, registry)


def _disambiguate_with_numeric_suffix(
    base_name: str,
    registry: ProjectRegistry,
) -> str:
    """Disambiguate name using numeric suffix fallback.

    Args:
        base_name: Base name to disambiguate
        registry: Registry to check for collisions

    Returns:
        Disambiguated name

    Raises:
        ValueError: If disambiguation fails after max attempts

    """
    i = 1
    while registry.get_by_name(f"{base_name}-{i}"):
        i += 1
        if i > MAX_DISAMBIGUATION_ATTEMPTS:
            msg = (
                f"Failed to disambiguate project name "
                f"after {MAX_DISAMBIGUATION_ATTEMPTS} attempts: {base_name}"
            )
            raise ValueError(msg)

    candidate = f"{base_name}-{i}"
    logger.info(
        "Successfully disambiguated '%s' to '%s' (strategy: numeric-suffix)",
        base_name,
        candidate,
    )
    return candidate


def _resolve_unique_name(
    path: Path,
    registry: ProjectRegistry,
) -> str:
    """Resolve a unique project name, handling collisions.

    Args:
        path: Project path
        registry: Registry to check for name collisions

    Returns:
        Unique project name

    Raises:
        ValueError: If name resolution fails

    """
    candidate_name = path.name
    existing_with_same_name = registry.get_by_name(candidate_name)

    if existing_with_same_name and existing_with_same_name.path != path:
        logger.info(
            "Name collision detected for '%s' (existing: %s, new: %s)",
            candidate_name,
            existing_with_same_name.path,
            path,
        )
        return _disambiguate_with_parent(path, path.name, registry)

    return candidate_name


class ProjectRegistryService:
    """Service for managing project registration and discovery.

    Handles persistence, CRUD operations, and automatic project discovery.
    """

    # Directories to skip during discovery
    SKIP_DIRS: ClassVar[set[str]] = {
        ".git",
        "node_modules",
        "venv",
        "__pycache__",
        "target",
        "build",
        ".venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "egg-info",
    }

    def __init__(self, registry_path: Path) -> None:
        """Initialize the registry service.

        Args:
            registry_path: Path to the registry JSON file

        """
        self.registry_path = registry_path
        self._registry: ProjectRegistry | None = None

    def _load(self) -> ProjectRegistry:
        """Load registry from disk.

        Note: This loads the entire registry into memory. For the default limit
        of 10,000 projects with ~500 bytes per project, this is approximately
        5MB of RAM, which is acceptable. Lazy loading/streaming was considered
        but deemed unnecessary given:
        - Default limit prevents unbounded growth
        - 10k projects ≈ 5-10MB RAM (well under 100MB requirement)
        - JSON format makes streaming complex without significant benefit

        Returns:
            The loaded registry, or empty registry if file doesn't exist

        """
        if not self.registry_path.exists():
            logger.debug("Registry file not found, creating empty registry")
            return ProjectRegistry()

        try:
            with self.registry_path.open("r") as f:
                data = json.load(f)
            registry = ProjectRegistry.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            logger.exception("Failed to load registry from %s", self.registry_path)
            # Back up corrupted file
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S%f")
            backup_path = self.registry_path.with_stem(
                f"{self.registry_path.stem}.corrupted.{timestamp}",
            )
            self.registry_path.replace(backup_path)
            logger.warning("Backed up corrupted registry to %s", backup_path)
            logger.warning("Creating new empty registry")
            return ProjectRegistry()
        else:
            logger.debug("Loaded registry with %d projects", len(registry.projects))
            return registry

    def _save(self, registry: ProjectRegistry) -> None:
        """Save registry to disk atomically.

        Args:
            registry: The registry to save

        """
        # Ensure parent directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_path = self.registry_path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                json_data = registry.model_dump(mode="json")
                json.dump(json_data, f, indent=2, default=str)
            temp_path.replace(self.registry_path)
            logger.debug("Saved registry with %d projects", len(registry.projects))
        except Exception:
            logger.exception("Failed to save registry to %s", self.registry_path)
            if temp_path.exists():
                temp_path.unlink()
            raise

    @property
    def registry(self) -> ProjectRegistry:
        """Get the current registry (lazy-loaded)."""
        if self._registry is None:
            self._registry = self._load()
        return self._registry

    def register_project(self, path: Path) -> ProjectMetadata:
        """Register a project in the registry.

        Args:
            path: Path to the project directory (containing .tasky/)

        Returns:
            The registered project metadata

        Raises:
            ValueError: If path doesn't exist or doesn't contain .tasky/,
                or if registry size limit is exceeded

        """
        path = _validate_project_path(path)
        registry = self.registry

        # Check if updating existing project
        existing = registry.get_by_path(path)
        if existing is None:
            _check_registry_size_limits(len(registry.projects))

        # Resolve unique name
        candidate_name = _resolve_unique_name(path, registry)

        # Create or update project metadata
        project = ProjectMetadata(
            name=candidate_name,
            path=path,
        )

        registry.add_or_update(project)
        self._save(registry)

        logger.info("Registered project: %s at %s", project.name, project.path)
        return project

    def unregister_project(self, path: Path) -> None:
        """Remove a project from the registry.

        Args:
            path: Path to the project directory

        Raises:
            ValueError: If project is not registered

        """
        path = path.resolve()
        registry = self.registry

        if not registry.remove(path):
            msg = f"Project not found in registry: {path}"
            raise ValueError(msg)

        self._save(registry)
        logger.info("Unregistered project: %s", path)

    def get_project(self, name: str) -> ProjectMetadata | None:
        """Get a project by name.

        Args:
            name: The project name

        Returns:
            Project metadata if found, None otherwise

        """
        return self.registry.get_by_name(name)

    def list_projects(self, *, limit: int | None = None, offset: int = 0) -> list[ProjectMetadata]:
        """List registered projects with optional pagination.

        Projects are sorted by last accessed (most recent first) before
        pagination is applied.

        Args:
            limit: Maximum number of projects to return (None = no limit)
            offset: Number of projects to skip (default: 0)

        Returns:
            List of project metadata, paginated and sorted by last accessed

        """
        projects = self.registry.projects.copy()
        projects.sort(key=lambda p: p.last_accessed, reverse=True)

        # Apply pagination
        if offset > 0:
            projects = projects[offset:]
        if limit is not None:
            projects = projects[:limit]

        return projects

    def update_last_accessed(self, path: Path) -> None:
        """Update the last accessed timestamp for a project.

        Args:
            path: Path to the project directory

        Raises:
            ValueError: If project is not found in registry

        """
        path = path.resolve()
        registry = self.registry
        project = registry.get_by_path(path)

        if not project:
            msg = f"Project not found: {path}"
            raise ValueError(msg)

        project.last_accessed = datetime.now(tz=UTC)
        self._save(registry)
        logger.debug("Updated last accessed for project: %s", path)

    def _walk_directories(
        self,
        root: Path,
        max_depth: int = 3,
    ) -> Iterator[Path]:
        """Walk directories recursively, skipping common non-project dirs."""
        yield from self._walk_directory_tree(root, max_depth=max_depth, depth=0)

    def _walk_directory_tree(
        self,
        current: Path,
        *,
        max_depth: int,
        depth: int,
    ) -> Iterator[Path]:
        """Yield directories depth-first up to ``max_depth``."""
        yield current
        if depth >= max_depth:
            return
        for child in self._iter_directory_children(current):
            yield from self._walk_directory_tree(
                child,
                max_depth=max_depth,
                depth=depth + 1,
            )

    def _iter_directory_children(self, current: Path) -> Iterator[Path]:
        """Iterate over child directories, handling errors and skip rules."""
        if not current.is_dir():
            return
        try:
            for item in current.iterdir():
                if self._should_skip_directory(item):
                    continue
                yield item
        except OSError:
            logger.warning("Unable to list directory: %s", current)

    def _should_skip_directory(self, item: Path) -> bool:
        """Return True if a directory should be skipped during traversal."""
        if not item.is_dir() or item.is_symlink():
            return True
        if item.name.startswith(".") and item.name != ".tasky":
            return True
        return item.name in self.SKIP_DIRS

    def discover_projects(
        self,
        search_paths: list[Path],
        progress_callback: Callable[[int], None] | None = None,
    ) -> list[ProjectMetadata]:
        """Discover projects in the given search paths.

        Args:
            search_paths: List of paths to search for projects
            progress_callback: Optional callable that receives directories_checked
                for progress updates

        Returns:
            List of discovered project metadata (deduplicated)

        """
        discovered: dict[Path, ProjectMetadata] = {}
        directories_checked = 0

        for search_path in search_paths:
            if not search_path.exists():
                logger.debug("Search path does not exist: %s", search_path)
                continue

            logger.info("Discovering projects in: %s", search_path)

            for directory in self._walk_directories(search_path):
                directories_checked += 1
                if progress_callback:
                    progress_callback(directories_checked)

                tasky_dir = directory / ".tasky"
                if tasky_dir.exists() and tasky_dir.is_dir():
                    # Found a project
                    project_path = directory.resolve()
                    if project_path not in discovered:
                        try:
                            metadata = ProjectMetadata(
                                name=project_path.name,
                                path=project_path,
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.warning(
                                "Skipping invalid project at %s: %s",
                                project_path,
                                exc,
                            )
                            continue
                        discovered[project_path] = metadata
                        logger.debug("Discovered project: %s", project_path)

        return list(discovered.values())

    def discover_and_register(
        self,
        search_paths: list[Path],
        progress_callback: Callable[[int], None] | None = None,
    ) -> int:
        """Discover and register projects in the given paths.

        Args:
            search_paths: List of paths to search for projects
            progress_callback: Optional callable that receives directories_checked
                for progress updates

        Returns:
            Number of newly registered projects

        """
        discovered = self.discover_projects(search_paths, progress_callback)
        registry = self.registry
        new_count = 0

        for project in discovered:
            is_new = registry.add_or_update(project)
            if is_new:
                new_count += 1

        if discovered:
            self._save(registry)
            logger.info(
                "Discovered %d projects, registered %d new",
                len(discovered),
                new_count,
            )

        return new_count
