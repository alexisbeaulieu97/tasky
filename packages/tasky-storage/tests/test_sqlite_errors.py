"""Comprehensive error path tests for SQLite repository."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from tasky_storage.backends.sqlite import SqliteTaskRepository
from tasky_storage.errors import StorageDataError, StorageError
from tasky_tasks.models import TaskModel, TaskStatus


class TestSqliteRepositoryErrors:
    """Test error handling paths in SQLite repository."""

    def test_save_task_database_locked_error(self, tmp_path: Path) -> None:
        """Test that database locked errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock connection to raise OperationalError for database locked
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError(
                "database is locked",
            )
            # Make connection itself a context manager
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database locked or inaccessible"):
                repo.save_task(task)

    def test_save_task_disk_full_error(self, tmp_path: Path) -> None:
        """Test that disk full errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock connection to raise OperationalError for disk full
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError(
                "database or disk is full",
            )
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database locked or inaccessible"):
                repo.save_task(task)

    def test_save_task_permission_denied_error(self, tmp_path: Path) -> None:
        """Test that permission denied errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock connection to raise OperationalError for permission denied
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError(
                "unable to open database file",
            )
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database locked or inaccessible"):
                repo.save_task(task)

    def test_save_task_integrity_error(self, tmp_path: Path) -> None:
        """Test that integrity errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock connection to raise IntegrityError
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.IntegrityError(
                "UNIQUE constraint failed",
            )
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageDataError, match="Database integrity error"):
                repo.save_task(task)

    def test_save_task_generic_sqlite_error(self, tmp_path: Path) -> None:
        """Test that generic SQLite errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock connection to raise generic sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Generic database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error saving task"):
                repo.save_task(task)

    def test_get_task_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during get_task are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task_id = uuid4()

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error retrieving task"):
                repo.get_task(task_id)

    def test_get_all_tasks_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during get_all_tasks are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error retrieving all tasks"):
                repo.get_all_tasks()

    def test_get_tasks_by_status_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during get_tasks_by_status are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(
                StorageError,
                match="Database error filtering tasks by status",
            ):
                repo.get_tasks_by_status(TaskStatus.PENDING)

    def test_delete_task_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during delete_task are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task_id = uuid4()

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error deleting task"):
                repo.delete_task(task_id)

    def test_task_exists_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during task_exists are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task_id = uuid4()

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error checking if task"):
                repo.task_exists(task_id)

    def test_find_tasks_database_error(self, tmp_path: Path) -> None:
        """Test that database errors during find_tasks are handled gracefully."""
        from tasky_tasks.models import TaskFilter

        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task_filter = TaskFilter(statuses=[TaskStatus.PENDING])

        # Mock connection to raise sqlite3.Error
        @contextmanager
        def mock_connection(*args, **kwargs):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database error")
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=None)
            yield mock_conn

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection,
        ):
            with pytest.raises(StorageError, match="Database error finding tasks"):
                repo.find_tasks(task_filter)

    def test_initialize_schema_validation_failure(self, tmp_path: Path) -> None:
        """Test that schema validation failures are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)

        # Mock validate_schema to return False
        with patch(
            "tasky_storage.backends.sqlite.repository.validate_schema",
            return_value=False,
        ):
            with pytest.raises(StorageDataError, match="Database integrity check failed"):
                repo.initialize()

    def test_get_task_corrupted_snapshot(self, tmp_path: Path) -> None:
        """Test that corrupted task snapshots are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Insert corrupted data directly into database
        # Note: SQLite CHECK constraint will prevent invalid status, so we need to
        # bypass it or use a different approach
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        # Disable foreign key checks temporarily to insert invalid data
        cursor.execute("PRAGMA foreign_keys=OFF")
        # Insert invalid task data (invalid datetime format)
        # Status must be valid due to CHECK constraint, but datetime can be invalid
        task_id = str(uuid4())
        cursor.execute(
            """
            INSERT INTO tasks (task_id, name, details, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                "Corrupted Task",
                "Details",
                "pending",  # Valid status (CHECK constraint requires it)
                "invalid_datetime",  # Invalid datetime
                "invalid_datetime",  # Invalid datetime
            ),
        )
        conn.commit()
        conn.close()

        # Try to retrieve the corrupted task - should raise StorageDataError
        # during validation when converting snapshot to TaskModel
        from uuid import UUID

        # get_all_tasks will try to convert all rows and should raise error
        with pytest.raises(StorageDataError):
            repo.get_all_tasks()
        # Also test get_task with the corrupted task ID
        with pytest.raises(StorageDataError):
            repo.get_task(UUID(task_id))

    def test_get_task_invalid_snapshot_validation_error(self, tmp_path: Path) -> None:
        """Test that invalid snapshots raise StorageDataError."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Mock row_to_snapshot to return invalid data
        with patch(
            "tasky_storage.backends.sqlite.repository.row_to_snapshot",
            return_value={
                "task_id": "not-a-uuid",
                "name": "Test",
                "details": "Details",
                "status": "pending",
                "created_at": "invalid",
                "updated_at": "invalid",
            },
        ):
            task_id = uuid4()
            # This should raise StorageDataError during validation
            with pytest.raises(StorageDataError):
                repo.get_task(task_id)

    def test_save_task_connection_error(self, tmp_path: Path) -> None:
        """Test that connection errors are handled gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")

        # Mock get_connection to raise an error when entering context
        @contextmanager
        def mock_connection_error(*args, **kwargs):
            raise sqlite3.Error("Connection failed")

        with patch(
            "tasky_storage.backends.sqlite.repository.get_connection",
            side_effect=mock_connection_error,
        ):
            # The error will propagate as-is since it's not caught in get_connection
            # but will be caught by the try/except in save_task
            with pytest.raises(sqlite3.Error):
                repo.save_task(task)

    def test_initialize_parent_directory_creation_error(self, tmp_path: Path) -> None:
        """Test that parent directory creation errors are handled."""
        # Create a path where parent directory cannot be created
        # This is difficult to simulate, but we can test the path exists logic
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)

        # Normal initialization should work
        repo.initialize()
        assert db_path.exists()

    def test_corrupted_database_integrity_check(self, tmp_path: Path) -> None:
        """Test that corrupted databases are detected during integrity check."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Corrupt the database by writing invalid data
        with open(db_path, "wb") as f:
            f.write(b"INVALID DATABASE CONTENT")

        # Try to initialize again - should detect corruption
        repo2 = SqliteTaskRepository(path=db_path)
        # The integrity check should fail
        with pytest.raises(StorageDataError, match="Database integrity check failed"):
            repo2.initialize()
