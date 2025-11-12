"""Tests for backend registry."""

from pathlib import Path

import pytest
from tasky_settings import BackendRegistry, registry


class MockRepository:
    """Mock repository for testing."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        """Initialize storage."""

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


def dummy_factory(path: Path) -> object:
    """Create a dummy repository."""
    return MockRepository(path)


def test_registry_register_and_get() -> None:
    """Test registering and retrieving a backend."""
    reg = BackendRegistry()
    reg.register("test", dummy_factory)

    factory = reg.get("test")
    assert factory is dummy_factory


def test_registry_register_multiple_backends() -> None:
    """Test registering multiple backends."""
    reg = BackendRegistry()

    def factory1(path: Path) -> object:
        return MockRepository(path)

    def factory2(path: Path) -> object:
        return MockRepository(path)

    reg.register("backend1", factory1)
    reg.register("backend2", factory2)

    assert reg.get("backend1") is factory1
    assert reg.get("backend2") is factory2


def test_registry_overwrite_existing_backend() -> None:
    """Test overwriting an existing backend registration."""
    reg = BackendRegistry()

    def factory1(path: Path) -> object:
        return MockRepository(path)

    def factory2(path: Path) -> object:
        return MockRepository(path)

    reg.register("test", factory1)
    reg.register("test", factory2)  # Overwrite

    assert reg.get("test") is factory2


def test_registry_get_unregistered_backend_raises_keyerror() -> None:
    """Test that get() raises KeyError for unregistered backend."""
    reg = BackendRegistry()

    with pytest.raises(KeyError, match="Backend 'nonexistent' not registered"):
        reg.get("nonexistent")


def test_registry_get_unregistered_shows_available_backends() -> None:
    """Test that error message lists available backends."""
    reg = BackendRegistry()
    reg.register("json", dummy_factory)
    reg.register("sqlite", dummy_factory)

    with pytest.raises(KeyError, match="Available backends: json, sqlite"):
        reg.get("postgres")


def test_registry_get_unregistered_shows_none_when_empty() -> None:
    """Test that error message shows 'none' when registry is empty."""
    reg = BackendRegistry()

    with pytest.raises(KeyError, match="Available backends: none"):
        reg.get("anything")


def test_registry_list_backends_returns_sorted_names() -> None:
    """Test list_backends() returns sorted backend names."""
    reg = BackendRegistry()
    reg.register("sqlite", dummy_factory)
    reg.register("json", dummy_factory)
    reg.register("postgres", dummy_factory)

    backends = reg.list_backends()
    assert backends == ["json", "postgres", "sqlite"]


def test_registry_list_backends_empty() -> None:
    """Test list_backends() returns empty list when no backends registered."""
    reg = BackendRegistry()
    assert reg.list_backends() == []


def test_global_registry_singleton() -> None:
    """Test that global registry singleton is accessible."""
    assert isinstance(registry, BackendRegistry)
    # Test that the import is consistent
    assert registry.list_backends() == registry.list_backends()
