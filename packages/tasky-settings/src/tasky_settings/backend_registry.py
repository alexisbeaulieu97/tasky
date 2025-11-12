"""Backend registry for storage backends."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tasky_tasks.ports import TaskRepository

    # Type alias for backend factory functions - used for type checking only
    BackendFactory = Callable[[Path], TaskRepository]
else:
    # At runtime, we use Any to avoid import issues
    BackendFactory = Callable[[Path], Any]


class BackendRegistry:
    """Registry for storage backend factories.

    Provides a plugin-style system where backends can register themselves
    with factory functions that create repository instances.

    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._backends: dict[str, Callable[[Path], Any]] = {}

    def register(self, name: str, factory: Callable[[Path], Any]) -> None:
        """Register a backend factory.

        Args:
            name: Backend name (e.g., "json", "sqlite")
            factory: Factory function that takes a Path and returns TaskRepository

        """
        self._backends[name] = factory

    def get(self, name: str) -> Callable[[Path], Any]:
        """Get a backend factory by name.

        Args:
            name: Backend name

        Returns:
            Backend factory function

        Raises:
            KeyError: If backend is not registered

        """
        if name not in self._backends:
            available = ", ".join(sorted(self._backends.keys())) or "none"
            msg = f"Backend '{name}' not registered. Available backends: {available}"
            raise KeyError(msg)
        return self._backends[name]

    def list_backends(self) -> list[str]:
        """Get list of registered backend names.

        Returns:
            Sorted list of backend names

        """
        return sorted(self._backends.keys())


# Global registry instance
registry = BackendRegistry()
