"""Tasky storage infrastructure for task persistence."""

from .backends.json import JsonStorage, JsonTaskRepository, TaskDocument
from .errors import StorageConfigurationError, StorageDataError, StorageError

__all__ = [
    "JsonStorage",
    "JsonTaskRepository",
    "StorageConfigurationError",
    "StorageDataError",
    "StorageError",
    "TaskDocument",
]

# Register JSON backend with the global registry
# This runs at import time, allowing the backend to be used by the factory
try:
    from tasky_settings import registry

    registry.register("json", JsonTaskRepository.from_path)
except ImportError:
    # tasky-settings may not be installed yet (e.g., during development)
    pass
