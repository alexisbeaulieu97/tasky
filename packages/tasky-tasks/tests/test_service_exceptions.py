"""Tests for TaskService exception behaviour."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from tasky_tasks.exceptions import TaskNotFoundError, TaskValidationError
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus
from tasky_tasks.service import TaskService

if TYPE_CHECKING:
    from uuid import UUID

try:
    from tasky_storage.errors import StorageDataError
except ModuleNotFoundError:  # pragma: no cover
    StorageDataError = type("StorageDataError", (Exception,), {})  # type: ignore[misc,assignment]


class _FakeRepository:
    """Minimal fake repository for testing."""

    def __init__(
        self,
        *,
        return_none: bool = False,
        raise_data_error: bool = False,
        task: TaskModel | None = None,
    ) -> None:
        self._return_none = return_none
        self._raise_data_error = raise_data_error
        self._task = task

    def initialize(self) -> None:
        """No-op initialization."""

    def save_task(self, task: TaskModel) -> None:
        """No-op save."""

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Return task or None based on configuration."""
        if self._raise_data_error:
            message = "corrupt task payload"
            raise StorageDataError(message)  # type: ignore[misc]
        if self._return_none:
            return None
        if self._task and self._task.task_id == task_id:
            return self._task
        return None

    def get_all_tasks(self) -> list[TaskModel]:
        """Return empty list or single task."""
        if self._task:
            return [self._task]
        return []

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Return tasks filtered by status."""
        if self._task and self._task.status == status:
            return [self._task]
        return []

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Return tasks matching the given filter."""
        if self._task and task_filter.matches(self._task):
            return [self._task]
        return []

    def delete_task(self, task_id: UUID) -> bool:
        """Return success status based on configuration."""
        if self._raise_data_error:
            message = "corrupt task payload"
            raise StorageDataError(message)  # type: ignore[misc]
        if self._task:
            return self._task.task_id == task_id
        return False

    def task_exists(self, task_id: UUID) -> bool:
        """Check if task exists."""
        if self._task:
            return self._task.task_id == task_id
        return False


def test_get_task_raises_task_not_found() -> None:
    """Service should raise TaskNotFoundError when repository returns None."""
    repository = _FakeRepository(return_none=True)
    service = TaskService(repository)
    task_id = uuid4()

    with pytest.raises(TaskNotFoundError) as exc_info:
        service.get_task(task_id)

    assert exc_info.value.task_id == task_id


def test_delete_task_raises_task_not_found_when_not_removed() -> None:
    """Service should raise TaskNotFoundError when delete fails."""
    repository = _FakeRepository(return_none=True)
    service = TaskService(repository)
    task_id = uuid4()

    with pytest.raises(TaskNotFoundError) as exc_info:
        service.delete_task(task_id)

    assert exc_info.value.task_id == task_id


def test_storage_data_error_translates_to_validation_error_on_get() -> None:
    """Storage data issues should surface as TaskValidationError."""
    repository = _FakeRepository(raise_data_error=True)
    service = TaskService(repository)

    with pytest.raises(TaskValidationError) as exc_info:
        service.get_task(uuid4())

    assert "invalid" in str(exc_info.value).lower()


def test_storage_data_error_translates_to_validation_error_on_delete() -> None:
    """Storage data issues should surface as TaskValidationError for delete."""
    repository = _FakeRepository(raise_data_error=True)
    service = TaskService(repository)

    with pytest.raises(TaskValidationError):
        service.delete_task(uuid4())


def test_successful_operations_do_not_raise() -> None:
    """Service should return values for successful operations."""
    task = TaskModel(name="Sample", details="Details")
    repository = _FakeRepository(task=task)
    service = TaskService(repository)

    retrieved = service.get_task(task.task_id)
    assert retrieved is task

    assert service.delete_task(task.task_id) is True
