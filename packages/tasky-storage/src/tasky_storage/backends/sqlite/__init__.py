"""SQLite storage backend for Tasky."""

from .repository import SqliteTaskRepository

__all__ = ["SqliteTaskRepository"]

# Backend Self-Registration
# Register this backend with the global registry on module import
try:
    from tasky_settings import registry

    registry.register("sqlite", SqliteTaskRepository.from_path)
except ImportError:
    # tasky-settings may not be installed yet (e.g., during development)
    pass
