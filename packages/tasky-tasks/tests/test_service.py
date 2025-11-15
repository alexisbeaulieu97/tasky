"""Tests for TaskService timestamp management."""

from __future__ import annotations

from datetime import UTC
from time import sleep
from uuid import UUID, uuid4

import pytest
from tasky_tasks.exceptions import InvalidStateTransitionError, TaskNotFoundError
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus
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

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Return tasks filtered by status."""
        return [task for task in self.tasks.values() if task.status == status]

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Return tasks matching the provided filter."""
        return [task for task in self.tasks.values() if task_filter.matches(task)]

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


class TestStateTransitionServiceMethods:
    """Test service-level state transition methods."""

    def test_complete_task_transitions_pending_to_completed(self) -> None:
        """Verify complete_task transitions a pending task to completed."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        original_updated = task.updated_at

        sleep(0.01)
        completed_task = service.complete_task(task.task_id)

        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.updated_at > original_updated
        assert repository.get_task(task.task_id)
        assert repository.get_task(task.task_id).status == TaskStatus.COMPLETED  # type: ignore[union-attr]

    def test_cancel_task_transitions_pending_to_cancelled(self) -> None:
        """Verify cancel_task transitions a pending task to cancelled."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        original_updated = task.updated_at

        sleep(0.01)
        cancelled_task = service.cancel_task(task.task_id)

        assert cancelled_task.status == TaskStatus.CANCELLED
        assert cancelled_task.updated_at > original_updated
        assert repository.get_task(task.task_id)
        assert repository.get_task(task.task_id).status == TaskStatus.CANCELLED  # type: ignore[union-attr]

    def test_reopen_task_transitions_completed_to_pending(self) -> None:
        """Verify reopen_task transitions a completed task to pending."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        service.complete_task(task.task_id)
        original_updated = repository.get_task(task.task_id).updated_at  # type: ignore[union-attr]

        sleep(0.01)
        reopened_task = service.reopen_task(task.task_id)

        assert reopened_task.status == TaskStatus.PENDING
        assert reopened_task.updated_at > original_updated
        assert repository.get_task(task.task_id)
        assert repository.get_task(task.task_id).status == TaskStatus.PENDING  # type: ignore[union-attr]

    def test_reopen_task_transitions_cancelled_to_pending(self) -> None:
        """Verify reopen_task transitions a cancelled task to pending."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        service.cancel_task(task.task_id)
        original_updated = repository.get_task(task.task_id).updated_at  # type: ignore[union-attr]

        sleep(0.01)
        reopened_task = service.reopen_task(task.task_id)

        assert reopened_task.status == TaskStatus.PENDING
        assert reopened_task.updated_at > original_updated
        assert repository.get_task(task.task_id)
        assert repository.get_task(task.task_id).status == TaskStatus.PENDING  # type: ignore[union-attr]

    def test_complete_task_raises_for_nonexistent_task(self) -> None:
        """Verify complete_task raises TaskNotFoundError for non-existent task."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)

        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError) as exc_info:
            service.complete_task(fake_id)

        assert exc_info.value.task_id == fake_id

    def test_cancel_task_raises_for_nonexistent_task(self) -> None:
        """Verify cancel_task raises TaskNotFoundError for non-existent task."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)

        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError) as exc_info:
            service.cancel_task(fake_id)

        assert exc_info.value.task_id == fake_id

    def test_reopen_task_raises_for_nonexistent_task(self) -> None:
        """Verify reopen_task raises TaskNotFoundError for non-existent task."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)

        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError) as exc_info:
            service.reopen_task(fake_id)

        assert exc_info.value.task_id == fake_id

    def test_complete_task_raises_for_invalid_transition(self) -> None:
        """Verify complete_task raises InvalidStateTransitionError for invalid transitions."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        service.cancel_task(task.task_id)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            service.complete_task(task.task_id)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.CANCELLED
        assert exc_info.value.to_status == TaskStatus.COMPLETED

    def test_cancel_task_raises_for_invalid_transition(self) -> None:
        """Verify cancel_task raises InvalidStateTransitionError for invalid transitions."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")
        service.complete_task(task.task_id)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            service.cancel_task(task.task_id)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.COMPLETED
        assert exc_info.value.to_status == TaskStatus.CANCELLED

    def test_reopen_task_raises_for_invalid_transition(self) -> None:
        """Verify reopen_task raises InvalidStateTransitionError for invalid transitions."""
        repository = InMemoryTaskRepository()
        service = TaskService(repository)
        task = service.create_task("Sample Task", "Details")

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            service.reopen_task(task.task_id)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.PENDING
        assert exc_info.value.to_status == TaskStatus.PENDING
