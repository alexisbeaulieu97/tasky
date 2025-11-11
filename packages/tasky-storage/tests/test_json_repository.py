"""Tests for the JsonTaskRepository in tasky-storage package."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from tasky_storage import JsonTaskRepository
from tasky_tasks.models import TaskModel, TaskStatus


@pytest.fixture
def repo(tmp_path: Path) -> JsonTaskRepository:
    """Provide an initialized JsonTaskRepository."""
    storage_path = tmp_path / "tasks.json"
    repository = JsonTaskRepository.from_path(storage_path)
    repository.initialize()
    return repository


class TestJsonTaskRepository:
    """Tests for the JsonTaskRepository class."""

    def test_initialize_creates_empty_document(self, tmp_path: Path) -> None:
        """Test that initialize creates an empty task document."""
        storage_path = tmp_path / "tasks.json"
        repo = JsonTaskRepository.from_path(storage_path)

        repo.initialize()

        assert repo.get_all_tasks() == []

    def test_save_and_get_task(self, repo: JsonTaskRepository) -> None:
        """Test saving and retrieving a task."""
        task = TaskModel(name="Test Task", details="Test details")

        repo.save_task(task)
        retrieved = repo.get_task(task.task_id)

        assert retrieved is not None
        assert retrieved.task_id == task.task_id
        assert retrieved.name == "Test Task"
        assert retrieved.details == "Test details"
        assert retrieved.status == TaskStatus.PENDING

    def test_get_nonexistent_task_returns_none(self, repo: JsonTaskRepository) -> None:
        """Test that getting a non-existent task returns None."""
        nonexistent_id = uuid4()

        task = repo.get_task(nonexistent_id)

        assert task is None

    def test_get_all_tasks(self, repo: JsonTaskRepository) -> None:
        """Test retrieving all tasks."""
        task1 = TaskModel(name="Task 1", details="Details 1")
        task2 = TaskModel(name="Task 2", details="Details 2")
        repo.save_task(task1)
        repo.save_task(task2)

        all_tasks = repo.get_all_tasks()

        assert len(all_tasks) == 2
        task_ids = {t.task_id for t in all_tasks}
        assert task1.task_id in task_ids
        assert task2.task_id in task_ids

    def test_get_all_tasks_returns_empty_list_when_uninitialized(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that get_all_tasks returns empty list for uninitialized repo."""
        storage_path = tmp_path / "nonexistent.json"
        repo = JsonTaskRepository.from_path(storage_path)

        all_tasks = repo.get_all_tasks()

        assert all_tasks == []

    def test_update_task(self, repo: JsonTaskRepository) -> None:
        """Test updating an existing task."""
        task = TaskModel(name="Original Name", details="Original details")
        repo.save_task(task)

        task.name = "Updated Name"
        task.details = "Updated details"
        task.status = TaskStatus.COMPLETED
        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.name == "Updated Name"
        assert retrieved.details == "Updated details"
        assert retrieved.status == TaskStatus.COMPLETED

    def test_delete_task(self, repo: JsonTaskRepository) -> None:
        """Test deleting a task."""
        task = TaskModel(name="Task to Delete", details="Will be deleted")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)

        deleted = repo.delete_task(task.task_id)

        assert deleted is True
        assert not repo.task_exists(task.task_id)
        assert repo.get_task(task.task_id) is None

    def test_delete_nonexistent_task(self, repo: JsonTaskRepository) -> None:
        """Test deleting a non-existent task."""
        nonexistent_id = uuid4()

        deleted = repo.delete_task(nonexistent_id)

        assert deleted is False

    def test_task_exists(self, repo: JsonTaskRepository) -> None:
        """Test checking if a task exists."""
        task = TaskModel(name="Existing Task", details="Exists")
        repo.save_task(task)

        assert repo.task_exists(task.task_id)
        assert not repo.task_exists(uuid4())

    def test_save_task_initializes_if_needed(self, tmp_path: Path) -> None:
        """Test that save_task initializes storage if not already initialized."""
        storage_path = tmp_path / "tasks.json"
        repo = JsonTaskRepository.from_path(storage_path)
        task = TaskModel(name="Auto Init Task", details="Should auto-initialize")

        repo.save_task(task)

        retrieved = repo.get_task(task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == task.task_id
