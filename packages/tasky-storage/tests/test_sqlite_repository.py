"""Tests for SQLite task repository implementation."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage.backends.sqlite import SqliteTaskRepository
from tasky_storage.errors import StorageDataError, StorageError
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


class TestSqliteTaskRepository:
    """Test suite for SqliteTaskRepository."""

    def test_initialize_creates_schema(self, tmp_path: Path) -> None:
        """Test that initialize creates database schema."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)

        repo.initialize()

        assert db_path.exists()

    def test_save_and_get_task(self, tmp_path: Path) -> None:
        """Test saving and retrieving a task."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")
        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == task.task_id
        assert retrieved.name == task.name
        assert retrieved.details == task.details
        assert retrieved.status == task.status

    def test_get_nonexistent_task_returns_none(self, tmp_path: Path) -> None:
        """Test retrieving a task that doesn't exist."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        result = repo.get_task(uuid4())
        assert result is None

    def test_get_all_tasks(self, tmp_path: Path) -> None:
        """Test retrieving all tasks."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task1 = TaskModel(name="Task 1", details="Details 1")
        task2 = TaskModel(name="Task 2", details="Details 2")
        repo.save_task(task1)
        repo.save_task(task2)

        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 2
        task_ids = {t.task_id for t in all_tasks}
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids

    def test_update_task(self, tmp_path: Path) -> None:
        """Test updating an existing task."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Original", details="Original details")
        repo.save_task(task)

        task.name = "Updated"
        task.mark_updated()
        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.name == "Updated"

    def test_delete_task(self, tmp_path: Path) -> None:
        """Test deleting a task."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="To Delete", details="Will be deleted")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)

        deleted = repo.delete_task(task.task_id)
        assert deleted is True
        assert not repo.task_exists(task.task_id)
        assert repo.get_task(task.task_id) is None

    def test_delete_nonexistent_task(self, tmp_path: Path) -> None:
        """Test deleting a task that doesn't exist."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        deleted = repo.delete_task(uuid4())
        assert deleted is False

    def test_task_exists(self, tmp_path: Path) -> None:
        """Test checking if a task exists."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)
        assert not repo.task_exists(uuid4())

    def test_get_tasks_by_status_pending(self, tmp_path: Path) -> None:
        """Test filtering tasks by pending status."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task1 = TaskModel(name="Pending 1", details="Details 1")
        task2 = TaskModel(name="Completed", details="Details 2")
        task2.complete()
        repo.save_task(task1)
        repo.save_task(task2)

        pending_tasks = repo.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 1
        assert pending_tasks[0].task_id == task1.task_id

    def test_get_tasks_by_status_completed(self, tmp_path: Path) -> None:
        """Test filtering tasks by completed status."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task1 = TaskModel(name="Pending", details="Details 1")
        task2 = TaskModel(name="Completed", details="Details 2")
        task2.complete()
        repo.save_task(task1)
        repo.save_task(task2)

        completed_tasks = repo.get_tasks_by_status(TaskStatus.COMPLETED)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].task_id == task2.task_id

    def test_get_tasks_by_status_cancelled(self, tmp_path: Path) -> None:
        """Test filtering tasks by cancelled status."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task1 = TaskModel(name="Pending", details="Details 1")
        task2 = TaskModel(name="Cancelled", details="Details 2")
        task2.cancel()
        repo.save_task(task1)
        repo.save_task(task2)

        cancelled_tasks = repo.get_tasks_by_status(TaskStatus.CANCELLED)
        assert len(cancelled_tasks) == 1
        assert cancelled_tasks[0].task_id == task2.task_id

    def test_get_tasks_by_status_empty_results(self, tmp_path: Path) -> None:
        """Test filtering when no tasks match the status."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Pending", details="Details")
        repo.save_task(task)

        completed_tasks = repo.get_tasks_by_status(TaskStatus.COMPLETED)
        assert len(completed_tasks) == 0

    def test_get_tasks_by_status_preserves_task_data(self, tmp_path: Path) -> None:
        """Test that filtering by status preserves all task data."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test Task", details="Test details")
        repo.save_task(task)

        tasks = repo.get_tasks_by_status(TaskStatus.PENDING)
        assert len(tasks) == 1
        retrieved = tasks[0]
        assert retrieved.task_id == task.task_id
        assert retrieved.name == task.name
        assert retrieved.details == task.details
        assert retrieved.status == TaskStatus.PENDING

    def test_from_path_factory(self, tmp_path: Path) -> None:
        """Test the from_path factory method."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository.from_path(db_path)

        assert db_path.exists()
        assert isinstance(repo, SqliteTaskRepository)

        # Verify it works
        task = TaskModel(name="Factory Test", details="Created via factory")
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None

    def test_initialize_idempotent(self, tmp_path: Path) -> None:
        """Test that calling initialize() multiple times doesn't fail."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)

        # First initialization
        repo.initialize()
        assert db_path.exists()

        # Second initialization should not raise
        repo.initialize()

        # Third initialization should also work
        repo.initialize()

        # Database should still be usable
        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None

    def test_schema_version_is_correct(self, tmp_path: Path) -> None:
        """Test that database has correct schema version."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Check schema version
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        conn.close()

        assert version == 1

    def test_concurrent_creates(self, tmp_path: Path) -> None:  # noqa: C901
        """Test multiple threads creating tasks simultaneously."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        created_tasks: list[TaskModel] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def create_tasks() -> None:
            try:
                for i in range(10):
                    task = TaskModel(
                        name=f"Task-{threading.current_thread().ident}-{i}",
                        details=f"Details {i}",
                    )
                    repo.save_task(task)
                    with lock:
                        created_tasks.append(task)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 10 threads
        threads = [threading.Thread(target=create_tasks) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent creates: {errors}"

        # Verify all tasks were created (10 threads x 10 tasks each)
        assert len(created_tasks) == 100

        # Verify all tasks exist in database
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 100

        # Verify task IDs match
        created_ids = {t.task_id for t in created_tasks}
        retrieved_ids = {t.task_id for t in all_tasks}
        assert created_ids == retrieved_ids

    def test_concurrent_read_write(self, tmp_path: Path) -> None:  # noqa: C901
        """Test concurrent reads while writes are happening."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial task
        initial_task = TaskModel(name="Initial", details="Initial task")
        repo.save_task(initial_task)

        errors: list[Exception] = []
        read_counts: list[int] = []
        lock = threading.Lock()

        def writer() -> None:
            try:
                for i in range(20):
                    task = TaskModel(name=f"Writer-{i}", details=f"Details {i}")
                    repo.save_task(task)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def reader() -> None:
            try:
                for _ in range(20):
                    tasks = repo.get_all_tasks()
                    with lock:
                        read_counts.append(len(tasks))
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 2 writer threads and 3 reader threads
        writer_threads = [threading.Thread(target=writer) for _ in range(2)]
        reader_threads = [threading.Thread(target=reader) for _ in range(3)]

        all_threads = writer_threads + reader_threads

        for thread in all_threads:
            thread.start()

        for thread in all_threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent read/write: {errors}"

        # Verify readers saw consistent data
        assert len(read_counts) == 60  # 3 readers x 20 reads
        assert all(count >= 1 for count in read_counts)

        # Verify final state
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 41  # 1 initial + 2 writers x 20

    def test_error_on_invalid_task_data(self, tmp_path: Path) -> None:
        """Test that schema constraints prevent invalid task data."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Attempting to insert invalid task data should fail
        # due to CHECK constraint on status
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # SQLite's CHECK constraint should prevent invalid status
        invalid_data = (
            "bad-id",
            "Test",
            "Details",
            "invalid_status",
            "2025-01-01T00:00:00",
            "2025-01-01T00:00:00",
        )
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO tasks (task_id, name, details, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                invalid_data,
            )
        conn.commit()
        conn.close()

        # Verify valid tasks can still be saved
        task = TaskModel(name="Valid Task", details="Valid details")
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None

    def test_database_integrity_check(self, tmp_path: Path) -> None:
        """Test that database integrity is validated on initialize."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Normal initialization should succeed
        assert db_path.exists()

        # Create a valid task to verify functionality
        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None

    def test_save_task_with_transaction(self, tmp_path: Path) -> None:
        """Test that save_task uses transactions."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Transaction Test", details="Testing transactions")
        repo.save_task(task)

        # Verify task persists
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None

        # Update and save again
        task.name = "Updated"
        task.mark_updated()
        repo.save_task(task)

        # Verify update persisted
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.name == "Updated"


class TestSqliteErrorPaths:
    """Test error handling and edge cases in SQLite repository."""

    def test_database_locked_error(self, tmp_path: Path) -> None:
        """Test handling of database locked errors."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create a task successfully first
        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)

        # Lock the database by holding a write transaction
        conn = sqlite3.connect(str(db_path))
        conn.execute("BEGIN EXCLUSIVE")

        # Try to save a task while database is locked
        # This should raise StorageError
        task2 = TaskModel(name="Locked", details="Will fail")
        with pytest.raises(StorageError, match="Database locked or inaccessible"):
            repo.save_task(task2)

        # Clean up
        conn.rollback()
        conn.close()

    def test_corrupted_task_snapshot_in_database(self, tmp_path: Path) -> None:
        """Test handling of corrupted task data during retrieval."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create a task with valid data first
        valid_task = TaskModel(name="Valid", details="Valid task")
        repo.save_task(valid_task)

        # Now corrupt the data by modifying the created_at to an invalid format
        # This bypasses the CHECK constraint but will fail during deserialization
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET created_at = ? WHERE task_id = ?",
            ("not-a-valid-datetime", str(valid_task.task_id)),
        )
        conn.commit()
        conn.close()

        # Trying to retrieve this task should raise StorageDataError
        with pytest.raises(StorageDataError):
            repo.get_task(valid_task.task_id)

    def test_find_tasks_with_corrupted_snapshot(self, tmp_path: Path) -> None:
        """Test that find_tasks handles corrupted task snapshots."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create valid task
        valid_task = TaskModel(name="Valid", details="Valid")
        repo.save_task(valid_task)

        # Corrupt the task data with invalid timestamp
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET updated_at = ? WHERE task_id = ?",
            ("invalid-timestamp", str(valid_task.task_id)),
        )
        conn.commit()
        conn.close()

        # find_tasks should raise StorageDataError when encountering corrupt data
        with pytest.raises(StorageDataError):
            repo.find_tasks(TaskFilter())

    def test_delete_with_database_error(self, tmp_path: Path) -> None:
        """Test delete_task handles database errors gracefully."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)

        # Lock the database
        conn = sqlite3.connect(str(db_path))
        conn.execute("BEGIN EXCLUSIVE")

        # Try to delete while locked
        with pytest.raises(StorageError, match="Database error deleting task"):
            repo.delete_task(task.task_id)

        conn.rollback()
        conn.close()

    def test_concurrent_modifications_serialization(self, tmp_path: Path) -> None:
        """Test that concurrent modifications are handled safely."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial task
        task = TaskModel(name="Original", details="Original details")
        repo.save_task(task)

        errors: list[Exception] = []
        lock = threading.Lock()

        def update_task(new_name: str) -> None:
            try:
                # Each thread gets its own connection
                updated = repo.get_task(task.task_id)
                if updated:
                    updated.name = new_name
                    updated.mark_updated()
                    repo.save_task(updated)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Launch multiple threads trying to update the same task
        threads = [threading.Thread(target=update_task, args=(f"Name-{i}",)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should complete without errors (last write wins)
        assert len(errors) == 0

        # Verify task exists and has one of the updated names
        final_task = repo.get_task(task.task_id)
        assert final_task is not None
        assert final_task.name.startswith("Name-")


class TestSqliteConcurrencyAndStress:
    """Test concurrency and stress scenarios for SQLite repository."""

    def test_high_volume_concurrent_writes(self, tmp_path: Path) -> None:
        """Test 10 threads each writing 50 tasks concurrently."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        errors: list[Exception] = []
        created_count = [0]
        lock = threading.Lock()

        def bulk_create(thread_id: int) -> None:
            try:
                for i in range(50):
                    task = TaskModel(
                        name=f"Task-T{thread_id}-{i}",
                        details=f"Bulk create test {i}",
                    )
                    repo.save_task(task)
                    with lock:
                        created_count[0] += 1
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # 10 threads x 50 tasks = 500 tasks
        threads = [threading.Thread(target=bulk_create, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors during bulk writes: {errors}"

        # Verify all tasks were created
        assert created_count[0] == 500

        # Verify database has all tasks
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 500

    def test_concurrent_read_heavy_workload(self, tmp_path: Path) -> None:
        """Test many concurrent readers with occasional writers."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial dataset
        for i in range(100):
            task = TaskModel(name=f"Initial-{i}", details=f"Task {i}")
            repo.save_task(task)

        errors: list[Exception] = []
        read_count = [0]
        write_count = [0]
        lock = threading.Lock()

        def reader() -> None:
            try:
                for _ in range(100):
                    tasks = repo.get_all_tasks()
                    assert len(tasks) >= 100
                    with lock:
                        read_count[0] += 1
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def writer() -> None:
            try:
                for i in range(10):
                    task = TaskModel(name=f"New-{i}", details=f"Added task {i}")
                    repo.save_task(task)
                    with lock:
                        write_count[0] += 1
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # 20 readers, 2 writers
        reader_threads = [threading.Thread(target=reader) for _ in range(20)]
        writer_threads = [threading.Thread(target=writer) for _ in range(2)]

        all_threads = reader_threads + writer_threads

        for thread in all_threads:
            thread.start()

        for thread in all_threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors during read-heavy workload: {errors}"

        # Verify all reads completed
        assert read_count[0] == 2000  # 20 readers x 100 reads

        # Verify all writes completed
        assert write_count[0] == 20  # 2 writers x 10 writes

        # Verify final database state
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 120  # 100 initial + 20 new

    def test_large_dataset_filtering_performance(self, tmp_path: Path) -> None:
        """Test filtering operations on a large dataset."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create 1000 tasks with various statuses
        for i in range(1000):
            task = TaskModel(name=f"Task-{i:04d}", details=f"Details {i}")
            if i % 3 == 0:
                task.complete()
            elif i % 5 == 0:
                task.cancel()
            repo.save_task(task)

        # Verify we can filter efficiently
        pending = repo.get_tasks_by_status(TaskStatus.PENDING)
        completed = repo.get_tasks_by_status(TaskStatus.COMPLETED)
        cancelled = repo.get_tasks_by_status(TaskStatus.CANCELLED)

        # Check counts are reasonable
        assert len(pending) > 0
        assert len(completed) > 0
        assert len(cancelled) > 0

        # Verify total matches
        total = len(pending) + len(completed) + len(cancelled)
        assert total == 1000

    def test_wal_mode_checkpoint_behavior(self, tmp_path: Path) -> None:
        """Test that WAL mode checkpoints work correctly under load."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Verify WAL mode is enabled
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        conn.close()

        assert mode.upper() == "WAL"

        # Create many tasks to trigger WAL growth
        for i in range(500):
            task = TaskModel(name=f"WAL-Test-{i}", details=f"Testing WAL {i}")
            repo.save_task(task)

        # Force a checkpoint
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()

        # Verify all data is still intact
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 500

    def test_long_transaction_handling(self, tmp_path: Path) -> None:
        """Test behavior with long-running read transactions."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial data
        for i in range(10):
            task = TaskModel(name=f"Initial-{i}", details="Initial")
            repo.save_task(task)

        # Start a long-running read transaction
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("BEGIN")
        cursor.execute("SELECT * FROM tasks")
        initial_rows = cursor.fetchall()

        # Write new tasks while read transaction is open
        for i in range(10):
            task = TaskModel(name=f"During-{i}", details="During transaction")
            repo.save_task(task)

        # Read transaction should still see old data (snapshot isolation)
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count_in_transaction = cursor.fetchone()[0]
        conn.rollback()
        conn.close()

        # Verify isolation (transaction sees 10 tasks)
        assert count_in_transaction == 10
        assert len(initial_rows) == 10

        # Verify new connection sees all 20 tasks
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 20

    def test_mixed_operation_concurrency(self, tmp_path: Path) -> None:
        """Test concurrent mix of create, read, update, and delete operations."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial dataset
        initial_tasks: list[TaskModel] = []
        for i in range(50):
            task = TaskModel(name=f"Initial-{i}", details=f"Task {i}")
            repo.save_task(task)
            initial_tasks.append(task)

        errors: list[Exception] = []
        lock = threading.Lock()

        def creator() -> None:
            try:
                for i in range(20):
                    task = TaskModel(name=f"Created-{i}", details=f"New task {i}")
                    repo.save_task(task)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def updater() -> None:
            try:
                for task in initial_tasks[:20]:
                    existing = repo.get_task(task.task_id)
                    if existing:
                        existing.name = f"Updated-{existing.name}"
                        existing.mark_updated()
                        repo.save_task(existing)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def deleter() -> None:
            try:
                for task in initial_tasks[40:]:
                    repo.delete_task(task.task_id)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def reader() -> None:
            try:
                for _ in range(50):
                    repo.get_all_tasks()
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Mix of operations
        threads = [
            threading.Thread(target=creator),
            threading.Thread(target=creator),
            threading.Thread(target=updater),
            threading.Thread(target=deleter),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors during mixed operations: {errors}"

        # Verify final state is consistent
        all_tasks = repo.get_all_tasks()
        # 50 initial - 10 deleted + 40 created = 80 tasks
        assert len(all_tasks) == 80
