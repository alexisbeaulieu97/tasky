"""Concurrency and stress tests for SQLite repository."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage.backends.sqlite import SqliteTaskRepository
from tasky_storage.backends.sqlite.connection import _connection_manager
from tasky_tasks.models import TaskModel, TaskStatus


class TestSqliteConcurrency:
    """Test concurrency and stress scenarios for SQLite repository."""

    def test_concurrent_writers_stress(self, tmp_path: Path) -> None:
        """Test 10 concurrent writers with proper synchronization."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        created_tasks: list[TaskModel] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def writer(thread_id: int, num_tasks: int = 10) -> None:
            """Write multiple tasks from a single thread."""
            try:
                for i in range(num_tasks):
                    task = TaskModel(
                        name=f"Task-{thread_id}-{i}",
                        details=f"Details from thread {thread_id}, task {i}",
                    )
                    repo.save_task(task)
                    with lock:
                        created_tasks.append(task)
                    # Small delay to increase chance of contention
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 10 writer threads
        threads = [threading.Thread(target=writer, args=(i, 10)) for i in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30.0)  # 30 second timeout
            assert not thread.is_alive(), "Thread did not complete in time"

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

        # Verify all tasks were created (10 threads x 10 tasks each)
        assert len(created_tasks) == 100

        # Verify all tasks exist in database
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 100

        # Verify task IDs match
        created_ids = {t.task_id for t in created_tasks}
        retrieved_ids = {t.task_id for t in all_tasks}
        assert created_ids == retrieved_ids

    def test_concurrent_read_write_mixed_workload(self, tmp_path: Path) -> None:
        """Test concurrent reads while writes are happening."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create initial tasks
        initial_tasks = [
            TaskModel(name=f"Initial-{i}", details=f"Initial task {i}")
            for i in range(5)
        ]
        for task in initial_tasks:
            repo.save_task(task)

        errors: list[Exception] = []
        read_results: list[int] = []
        write_count = [0]
        lock = threading.Lock()

        def writer(iterations: int = 20) -> None:
            """Write tasks concurrently."""
            try:
                for i in range(iterations):
                    task = TaskModel(
                        name=f"Writer-{threading.current_thread().ident}-{i}",
                        details=f"Concurrent write {i}",
                    )
                    repo.save_task(task)
                    with lock:
                        write_count[0] += 1
                    time.sleep(0.001)  # Small delay
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        def reader(iterations: int = 30) -> None:
            """Read tasks concurrently."""
            try:
                for _ in range(iterations):
                    tasks = repo.get_all_tasks()
                    with lock:
                        read_results.append(len(tasks))
                    time.sleep(0.001)  # Small delay
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 3 writer threads and 5 reader threads
        writer_threads = [
            threading.Thread(target=writer, args=(20,)) for _ in range(3)
        ]
        reader_threads = [
            threading.Thread(target=reader, args=(30,)) for _ in range(5)
        ]

        all_threads = writer_threads + reader_threads

        # Start all threads
        for thread in all_threads:
            thread.start()

        # Wait for all to complete
        for thread in all_threads:
            thread.join(timeout=30.0)
            assert not thread.is_alive(), "Thread did not complete in time"

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent read/write: {errors}"

        # Verify readers saw consistent data (at least initial tasks)
        assert len(read_results) == 150  # 5 readers x 30 reads
        assert all(count >= 5 for count in read_results), "Readers saw inconsistent data"

        # Verify final state
        all_tasks = repo.get_all_tasks()
        # Should have: 5 initial + 3 writers x 20 tasks = 65 tasks
        assert len(all_tasks) == 65
        assert write_count[0] == 60  # 3 writers x 20 tasks

    def test_concurrent_updates_same_task(self, tmp_path: Path) -> None:
        """Test concurrent updates to the same task."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create a single task
        task = TaskModel(name="Shared Task", details="Will be updated concurrently")
        repo.save_task(task)

        errors: list[Exception] = []
        update_count = [0]
        lock = threading.Lock()

        def updater(thread_id: int, iterations: int = 10) -> None:
            """Update the same task multiple times."""
            try:
                for i in range(iterations):
                    retrieved = repo.get_task(task.task_id)
                    if retrieved is not None:
                        retrieved.name = f"Updated-by-{thread_id}-{i}"
                        retrieved.mark_updated()
                        repo.save_task(retrieved)
                        with lock:
                            update_count[0] += 1
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 5 threads updating the same task
        threads = [
            threading.Thread(target=updater, args=(i, 10)) for i in range(5)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=30.0)
            assert not thread.is_alive(), "Thread did not complete in time"

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent updates: {errors}"

        # Verify task was updated (at least some updates succeeded)
        assert update_count[0] > 0

        # Verify final task state is consistent
        final_task = repo.get_task(task.task_id)
        assert final_task is not None
        assert final_task.task_id == task.task_id

    def test_concurrent_deletes(self, tmp_path: Path) -> None:
        """Test concurrent deletes of different tasks."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create many tasks
        tasks = [
            TaskModel(name=f"Task-{i}", details=f"Task {i} to be deleted")
            for i in range(50)
        ]
        for task in tasks:
            repo.save_task(task)

        errors: list[Exception] = []
        delete_count = [0]
        lock = threading.Lock()

        def deleter(task_ids: list, thread_id: int) -> None:
            """Delete tasks concurrently."""
            try:
                for task_id in task_ids:
                    deleted = repo.delete_task(task_id)
                    if deleted:
                        with lock:
                            delete_count[0] += 1
                    time.sleep(0.001)
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Split tasks among 5 threads
        threads = []
        tasks_per_thread = 10
        for i in range(5):
            start_idx = i * tasks_per_thread
            end_idx = start_idx + tasks_per_thread
            thread_task_ids = [t.task_id for t in tasks[start_idx:end_idx]]
            thread = threading.Thread(target=deleter, args=(thread_task_ids, i))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=30.0)
            assert not thread.is_alive(), "Thread did not complete in time"

        # Verify no errors
        assert len(errors) == 0, f"Errors during concurrent deletes: {errors}"

        # Verify all tasks were deleted
        assert delete_count[0] == 50

        # Verify no tasks remain
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 0

    def test_wal_mode_checkpoint_behavior(self, tmp_path: Path) -> None:
        """Test that WAL mode handles checkpoints correctly."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create many tasks to trigger WAL checkpoint
        tasks = [
            TaskModel(name=f"Task-{i}", details=f"Task {i} for WAL testing")
            for i in range(100)
        ]

        # Save all tasks
        for task in tasks:
            repo.save_task(task)

        # Verify all tasks are readable
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 100

        # Force a checkpoint by closing and reopening connection
        # (The connection manager will handle this)
        _connection_manager.close_all()

        # Verify data persists after checkpoint
        all_tasks_after = repo.get_all_tasks()
        assert len(all_tasks_after) == 100

    def test_connection_pool_exhaustion_recovery(self, tmp_path: Path) -> None:
        """Test recovery from connection pool exhaustion scenarios."""
        db_path = tmp_path / "tasks.db"
        repo = SqliteTaskRepository(path=db_path)
        repo.initialize()

        # Create many concurrent operations that might exhaust connections
        errors: list[Exception] = []
        success_count = [0]
        lock = threading.Lock()

        def intensive_operation(iterations: int = 50) -> None:
            """Perform many operations rapidly."""
            try:
                for i in range(iterations):
                    # Create a task
                    task = TaskModel(
                        name=f"Intensive-{threading.current_thread().ident}-{i}",
                        details=f"Intensive operation {i}",
                    )
                    repo.save_task(task)

                    # Read it back
                    retrieved = repo.get_task(task.task_id)
                    assert retrieved is not None

                    # Update it
                    retrieved.name = f"Updated-{i}"
                    retrieved.mark_updated()
                    repo.save_task(retrieved)

                    # Delete it
                    repo.delete_task(task.task_id)

                    with lock:
                        success_count[0] += 1
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(e)

        # Create 10 threads doing intensive operations
        threads = [
            threading.Thread(target=intensive_operation, args=(50,))
            for _ in range(10)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=60.0)  # Longer timeout for intensive operations
            assert not thread.is_alive(), "Thread did not complete in time"

        # Verify no errors (connection pool should handle this)
        assert len(errors) == 0, f"Errors during intensive operations: {errors}"

        # Verify operations succeeded
        assert success_count[0] == 500  # 10 threads x 50 iterations

        # Verify database is in consistent state
        all_tasks = repo.get_all_tasks()
        # All tasks should have been deleted
        assert len(all_tasks) == 0
