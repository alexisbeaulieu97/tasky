"""Tasky storage infrastructure for task persistence."""

from .backends.json import JsonStorage, JsonTaskRepository, TaskDocument
from .backends.sqlite import SqliteTaskRepository
from .errors import (
    SnapshotConversionError,
    StorageConfigurationError,
    StorageDataError,
    StorageError,
    StorageIOError,
    TransactionConflictError,
)

__all__ = [
    "JsonStorage",
    "JsonTaskRepository",
    "SnapshotConversionError",
    "SqliteTaskRepository",
    "StorageConfigurationError",
    "StorageDataError",
    "StorageError",
    "StorageIOError",
    "TaskDocument",
    "TransactionConflictError",
]

# ============================================================================
# Backend Self-Registration Pattern
# ============================================================================
#
# Storage backends register themselves at import time using the global registry
# from tasky_settings. This allows the service factory to discover backends
# without explicit coupling.
#
# Pattern for backend authors:
#   1. Import the registry: `from tasky_settings import registry`
#   2. Register your backend: `registry.register("name", factory_function)`
#   3. The factory function should accept a Path and return a TaskRepository
#
# The tasky_settings.factory module ensures this module is imported before
# accessing the registry, so backends are always available when needed.
#
# See existing backends (JsonTaskRepository, SqliteTaskRepository) for examples.
#
# ============================================================================

# Register JSON backend with the global registry
# This runs at import time, allowing the backend to be used by the factory
try:
    from tasky_settings import registry

    registry.register("json", JsonTaskRepository.from_path)
except ImportError:
    # tasky-settings may not be installed yet (e.g., during development)
    pass
