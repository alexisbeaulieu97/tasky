"""Tests for TaskService timestamp management."""

from __future__ import annotations

from datetime import UTC
from time import sleep
from uuid import UUID

from tasky_tasks.models import TaskModel
from tasky_tasks.service import TaskService


class InMemoryTaskRepository:
    """In-memory repository implementation for testing.

    Implements the TaskRepository protocol without requiring the full
    protocol definition import, avoiding circular dependencies.
    """

    def __init__(self) -> None:
        self.tasks: dict[UUID, TaskModel] = {}

    def initialize(self) -> None:
        """Reset the repository state."""
        self.tasks.clear()

    def save_task(self, task: TaskModel) -> None:
        """Persist a task."""
        self.tasks[task.task_id] = task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Return a stored task when present."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        """Return all stored tasks."""
        return list(self.tasks.values())

    def delete_task(self, task_id: UUID) -> bool:
        """Remove a stored task."""
        return self.tasks.pop(task_id, None) is not None

    def task_exists(self, task_id: UUID) -> bool:
        """Determine whether a task is stored."""
        return task_id in self.tasks


def test_create_task_sets_timestamps() -> None:
    """Verify service creates tasks with UTC timestamps."""
    repository = InMemoryTaskRepository()
    service = TaskService(repository)

    task = service.create_task("Sample Task", "Details")

    assert task.created_at.tzinfo == UTC
    assert task.updated_at.tzinfo == UTC
    assert task.created_at == task.updated_at
    assert repository.get_task(task.task_id) is task


def test_update_task_modifies_updated_at() -> None:
    """Verify service updates updated_at when saving changes."""
    repository = InMemoryTaskRepository()
    service = TaskService(repository)
    task = service.create_task("Sample Task", "Details")
    original_updated_at = task.updated_at

    sleep(0.01)
    task.details = "Updated Details"
    service.update_task(task)

    stored_task = repository.get_task(task.task_id)
    assert stored_task is not None
    assert stored_task.updated_at > original_updated_at
    assert stored_task.updated_at.tzinfo == UTC
    assert stored_task.created_at == task.created_at
