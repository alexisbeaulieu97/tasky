"""Tests for service factory."""

from pathlib import Path

import pytest
from tasky_settings import ProjectNotFoundError, create_task_service, find_project_root, registry


class MockRepository:
    """Mock repository for testing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.initialized = False

    def initialize(self) -> None:
        """Initialize storage."""
        self.initialized = True

    def save_task(self, task: object) -> None:
        """Save a task."""

    def get_task(self, task_id: object) -> object:  # noqa: ARG002
        """Get a task."""
        return None

    def get_all_tasks(self) -> list[object]:
        """Get all tasks."""
        return []

    def delete_task(self, task_id: object) -> bool:  # noqa: ARG002
        """Delete a task."""
        return False

    def task_exists(self, task_id: object) -> bool:  # noqa: ARG002
        """Check if task exists."""
        return False


def mock_factory(path: Path) -> object:
    """Create a mock repository."""
    return MockRepository(path)


def _create_config_file(config_dir: Path, backend: str = "mock", path: str = "tasks.json") -> None:
    """Create a TOML config file for testing."""
    config_file = config_dir / "config.toml"
    config_content = f'[storage]\nbackend = "{backend}"\npath = "{path}"\n'
    config_file.write_text(config_content)


def test_find_project_root_in_current_dir(tmp_path: Path) -> None:
    """Test find_project_root finds .tasky directory in current directory."""
    # Create .tasky directory in tmp_path
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()

    # Should find it
    root = find_project_root(tmp_path)
    assert root == tmp_path


def test_find_project_root_in_parent_dir(tmp_path: Path) -> None:
    """Test find_project_root walks up directory tree."""
    # Create .tasky directory in tmp_path
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()

    # Create subdirectory
    subdir = tmp_path / "subdir" / "nested"
    subdir.mkdir(parents=True)

    # Should find it from subdirectory
    root = find_project_root(subdir)
    assert root == tmp_path


def test_find_project_root_not_found(tmp_path: Path) -> None:
    """Test find_project_root raises ProjectNotFoundError."""
    # No .tasky directory
    with pytest.raises(ProjectNotFoundError) as exc_info:
        find_project_root(tmp_path)

    assert exc_info.value.start_path == tmp_path.resolve()
    assert "No project found" in str(exc_info.value)


def test_find_project_root_defaults_to_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test find_project_root uses current directory when start_path is None."""
    # Create .tasky directory in tmp_path
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()

    # Change to tmp_path
    monkeypatch.chdir(tmp_path)

    # Should find it without explicit path
    root = find_project_root()
    assert root == tmp_path


def test_create_task_service_with_explicit_root(tmp_path: Path) -> None:
    """Test create_task_service with explicit project_root."""
    # Register mock backend
    registry.register("mock", mock_factory)

    # Create config
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    _create_config_file(config_dir, backend="mock", path="tasks.db")

    # Create service
    service = create_task_service(tmp_path)

    assert service is not None
    assert service.repository is not None
    # Check repository was initialized
    assert service.repository.initialized  # type: ignore[attr-defined]
    # Check path was constructed correctly
    expected_path = tmp_path / ".tasky" / "tasks.db"
    assert service.repository.path == expected_path  # type: ignore[attr-defined]


def test_create_task_service_finds_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test create_task_service finds project without explicit root."""
    # Register mock backend
    registry.register("mock", mock_factory)

    # Create config
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    _create_config_file(config_dir, backend="mock", path="tasks.json")

    # Change to project directory
    monkeypatch.chdir(tmp_path)

    # Create service without explicit root
    service = create_task_service()

    assert service is not None
    assert service.repository is not None


def test_create_task_service_no_project_raises_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test create_task_service raises ProjectNotFoundError."""
    # Change to tmp_path so walking up finds no project
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ProjectNotFoundError):
        create_task_service(tmp_path)


def test_create_task_service_invalid_backend_raises_keyerror(tmp_path: Path) -> None:
    """Test create_task_service raises KeyError for unregistered backend."""
    # Create config with unregistered backend
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    _create_config_file(config_dir, backend="nonexistent", path="tasks.json")

    # Should raise KeyError
    with pytest.raises(KeyError, match="Backend 'nonexistent' not registered"):
        create_task_service(tmp_path)


def test_create_task_service_constructs_absolute_path(tmp_path: Path) -> None:
    """Test create_task_service constructs absolute path from relative path."""
    # Register mock backend
    registry.register("mock", mock_factory)

    # Create config with relative path
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    _create_config_file(config_dir, backend="mock", path="nested/dir/tasks.db")

    # Create service
    service = create_task_service(tmp_path)

    # Check path is absolute
    expected_path = tmp_path / ".tasky" / "nested" / "dir" / "tasks.db"
    assert service.repository.path == expected_path  # type: ignore[attr-defined]


def test_create_task_service_calls_initialize(tmp_path: Path) -> None:
    """Test create_task_service calls repository.initialize()."""
    # Register mock backend
    registry.register("mock", mock_factory)

    # Create config
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    _create_config_file(config_dir, backend="mock", path="tasks.json")

    # Create service
    service = create_task_service(tmp_path)

    # Check initialize was called
    assert service.repository.initialized  # type: ignore[attr-defined]
