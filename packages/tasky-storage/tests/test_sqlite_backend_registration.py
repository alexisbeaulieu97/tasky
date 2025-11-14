"""Tests for backend registry integration with SQLite."""

from __future__ import annotations

from pathlib import Path

from tasky_settings import registry
from tasky_storage import SqliteTaskRepository


def test_sqlite_backend_registered() -> None:
    """Test that SQLite backend is registered on import."""
    backends = registry.list_backends()
    assert "sqlite" in backends
    assert "json" in backends


def test_sqlite_backend_factory_works(tmp_path: Path) -> None:
    """Test that SQLite backend factory creates working repository."""
    db_path = tmp_path / "test.db"
    factory = registry.get("sqlite")
    repo = factory(db_path)

    assert isinstance(repo, SqliteTaskRepository)
    assert db_path.exists()
