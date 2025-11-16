"""Parameterized tests ensuring identical behavior between JSON and SQLite backends."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage import JsonTaskRepository, SqliteTaskRepository
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


# Fixture to provide both repository types
@pytest.fixture(params=["json", "sqlite"])
def repo(request: pytest.FixtureRequest, tmp_path: Path):
    """Provide both JSON and SQLite repositories for parameterized testing."""
    if request.param == "json":
        storage_path = tmp_path / "tasks.json"
        repository = JsonTaskRepository.from_path(storage_path)
        repository.initialize()
        return repository
    else:  # sqlite
        db_path = tmp_path / "tasks.db"
        repository = SqliteTaskRepository.from_path(db_path)
        return repository


class TestCrossBackendBehavior:
    """Test that JSON and SQLite backends behave identically."""

    def test_save_and_retrieve_task(self, repo) -> None:
        """Test saving and retrieving tasks works identically."""
        task = TaskModel(name="Test Task", details="Test details")
        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == task.task_id
        assert retrieved.name == task.name
        assert retrieved.details == task.details
        assert retrieved.status == task.status

    def test_get_nonexistent_task(self, repo) -> None:
        """Test getting non-existent task returns None identically."""
        nonexistent_id = uuid4()
        result = repo.get_task(nonexistent_id)
        assert result is None

    def test_get_all_tasks(self, repo) -> None:
        """Test getting all tasks works identically."""
        task1 = TaskModel(name="Task 1", details="Details 1")
        task2 = TaskModel(name="Task 2", details="Details 2")
        task3 = TaskModel(name="Task 3", details="Details 3")

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 3

        task_ids = {t.task_id for t in all_tasks}
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids
        assert task3.task_id in task_ids

    def test_update_task(self, repo) -> None:
        """Test updating tasks works identically."""
        task = TaskModel(name="Original", details="Original details")
        repo.save_task(task)

        task.name = "Updated"
        task.details = "Updated details"
        task.mark_updated()
        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.name == "Updated"
        assert retrieved.details == "Updated details"

    def test_delete_task(self, repo) -> None:
        """Test deleting tasks works identically."""
        task = TaskModel(name="To Delete", details="Will be deleted")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)

        deleted = repo.delete_task(task.task_id)
        assert deleted is True
        assert not repo.task_exists(task.task_id)
        assert repo.get_task(task.task_id) is None

    def test_delete_nonexistent_task(self, repo) -> None:
        """Test deleting non-existent task returns False identically."""
        nonexistent_id = uuid4()
        deleted = repo.delete_task(nonexistent_id)
        assert deleted is False

    def test_task_exists(self, repo) -> None:
        """Test task_exists works identically."""
        task = TaskModel(name="Existing", details="Exists")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)
        assert not repo.task_exists(uuid4())

    def test_get_tasks_by_status_pending(self, repo) -> None:
        """Test filtering by pending status works identically."""
        task1 = TaskModel(name="Pending 1", details="Details")
        task2 = TaskModel(name="Pending 2", details="Details")
        task3 = TaskModel(name="Completed", details="Details")
        task3.complete()

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        pending_tasks = repo.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 2
        task_ids = {t.task_id for t in pending_tasks}
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids
        assert task3.task_id not in task_ids

    def test_get_tasks_by_status_completed(self, repo) -> None:
        """Test filtering by completed status works identically."""
        task1 = TaskModel(name="Pending", details="Details")
        task2 = TaskModel(name="Completed 1", details="Details")
        task2.complete()
        task3 = TaskModel(name="Completed 2", details="Details")
        task3.complete()

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        completed_tasks = repo.get_tasks_by_status(TaskStatus.COMPLETED)
        assert len(completed_tasks) == 2
        assert all(task.status == TaskStatus.COMPLETED for task in completed_tasks)

    def test_get_tasks_by_status_cancelled(self, repo) -> None:
        """Test filtering by cancelled status works identically."""
        task1 = TaskModel(name="Pending", details="Details")
        task2 = TaskModel(name="Cancelled", details="Details")
        task2.cancel()

        repo.save_task(task1)
        repo.save_task(task2)

        cancelled_tasks = repo.get_tasks_by_status(TaskStatus.CANCELLED)
        assert len(cancelled_tasks) == 1
        assert cancelled_tasks[0].status == TaskStatus.CANCELLED

    def test_get_tasks_by_status_empty_results(self, repo) -> None:
        """Test filtering with no matches works identically."""
        task = TaskModel(name="Pending", details="Details")
        repo.save_task(task)

        completed_tasks = repo.get_tasks_by_status(TaskStatus.COMPLETED)
        cancelled_tasks = repo.get_tasks_by_status(TaskStatus.CANCELLED)

        assert completed_tasks == []
        assert cancelled_tasks == []

    def test_find_tasks_by_status(self, repo) -> None:
        """Test find_tasks with status filter works identically."""
        task1 = TaskModel(name="Pending 1", details="Details")
        task2 = TaskModel(name="Pending 2", details="Details")
        task3 = TaskModel(name="Completed", details="Details")
        task3.complete()

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        filter_pending = TaskFilter(statuses=[TaskStatus.PENDING])
        pending_tasks = repo.find_tasks(filter_pending)

        assert len(pending_tasks) == 2
        assert all(task.status == TaskStatus.PENDING for task in pending_tasks)

    def test_find_tasks_by_multiple_statuses(self, repo) -> None:
        """Test find_tasks with multiple statuses works identically."""
        task1 = TaskModel(name="Pending", details="Details")
        task2 = TaskModel(name="Completed 1", details="Details")
        task2.complete()
        task3 = TaskModel(name="Completed 2", details="Details")
        task3.complete()
        task4 = TaskModel(name="Cancelled", details="Details")
        task4.cancel()

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)
        repo.save_task(task4)

        filter_multiple = TaskFilter(
            statuses=[TaskStatus.PENDING, TaskStatus.COMPLETED],
        )
        filtered_tasks = repo.find_tasks(filter_multiple)

        assert len(filtered_tasks) == 3
        statuses = {task.status for task in filtered_tasks}
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.COMPLETED in statuses
        assert TaskStatus.CANCELLED not in statuses

    def test_find_tasks_empty_status_list(self, repo) -> None:
        """Test find_tasks with empty status list returns empty identically."""
        task = TaskModel(name="Task", details="Details")
        repo.save_task(task)

        filter_empty = TaskFilter(statuses=[])
        filtered_tasks = repo.find_tasks(filter_empty)

        assert filtered_tasks == []

    def test_find_tasks_by_name_contains(self, repo) -> None:
        """Test find_tasks with name_contains filter works identically."""
        task1 = TaskModel(name="Python Task", details="Details")
        task2 = TaskModel(name="Java Task", details="Details")
        task3 = TaskModel(name="Python Script", details="Details")

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        filter_python = TaskFilter(name_contains="Python")
        python_tasks = repo.find_tasks(filter_python)

        assert len(python_tasks) == 2
        assert all("Python" in task.name for task in python_tasks)

    def test_find_tasks_by_date_range(self, repo) -> None:
        """Test find_tasks with date range filter works identically."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        task1 = TaskModel(name="Old Task", details="Details")
        # Manually set created_at to yesterday
        task1.created_at = yesterday
        task2 = TaskModel(name="Recent Task", details="Details")
        task3 = TaskModel(name="Future Task", details="Details")
        # Manually set created_at to tomorrow
        task3.created_at = tomorrow

        repo.save_task(task1)
        repo.save_task(task2)
        repo.save_task(task3)

        # Filter for tasks created after yesterday
        filter_recent = TaskFilter(created_after=yesterday)
        recent_tasks = repo.find_tasks(filter_recent)

        # Should include task2 and task3 (created at now and tomorrow)
        assert len(recent_tasks) >= 1
        assert any(task.name == "Recent Task" for task in recent_tasks)

    def test_multiple_operations_consistency(self, repo) -> None:
        """Test that multiple operations maintain consistency identically."""
        # Create tasks
        tasks = [
            TaskModel(name=f"Task {i}", details=f"Details {i}")
            for i in range(10)
        ]
        for task in tasks:
            repo.save_task(task)

        # Update some tasks
        for i in range(0, 10, 2):  # Update even-indexed tasks
            task = repo.get_task(tasks[i].task_id)
            assert task is not None
            task.name = f"Updated Task {i}"
            task.mark_updated()
            repo.save_task(task)

        # Complete some tasks
        for i in range(1, 10, 2):  # Complete odd-indexed tasks
            task = repo.get_task(tasks[i].task_id)
            assert task is not None
            task.complete()
            repo.save_task(task)

        # Delete some tasks
        for i in range(0, 5):  # Delete first 5 tasks
            repo.delete_task(tasks[i].task_id)

        # Verify final state
        all_tasks = repo.get_all_tasks()
        assert len(all_tasks) == 5  # 10 created - 5 deleted = 5 remaining

        # Verify remaining tasks
        remaining_ids = {t.task_id for t in all_tasks}
        for i in range(5, 10):
            assert tasks[i].task_id in remaining_ids

    def test_task_state_transitions(self, repo) -> None:
        """Test task state transitions work identically."""
        task = TaskModel(name="State Test", details="Testing state transitions")
        repo.save_task(task)

        # Pending -> Completed
        task.complete()
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.status == TaskStatus.COMPLETED

        # Completed -> Cancelled (via new task)
        task2 = TaskModel(name="Cancel Test", details="Testing cancel")
        repo.save_task(task2)
        task2.cancel()
        repo.save_task(task2)
        retrieved2 = repo.get_task(task2.task_id)
        assert retrieved2 is not None
        assert retrieved2.status == TaskStatus.CANCELLED

    def test_initialize_idempotent(self, repo) -> None:
        """Test that initialize is idempotent identically."""
        # Initialize multiple times should not fail
        if hasattr(repo, "initialize"):
            repo.initialize()
            repo.initialize()
            repo.initialize()

        # Repository should still be usable
        task = TaskModel(name="Test", details="Test")
        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
