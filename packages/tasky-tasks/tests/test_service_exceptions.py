"""Tests for TaskService exception behaviour."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from tasky_tasks.exceptions import TaskNotFoundError, TaskValidationError
from tasky_tasks.models import TaskModel
from tasky_tasks.service import TaskService

try:
    from tasky_storage.errors import StorageDataError
except ModuleNotFoundError:  # pragma: no cover

    class StorageDataError(Exception):
        """Fallback storage data error when storage package is unavailable."""


def _not_found_repository() -> SimpleNamespace:
    return SimpleNamespace(
        initialize=lambda: None,
        save_task=lambda _task: None,
        get_task=lambda _task_id: None,
        get_all_tasks=list,
        delete_task=lambda _task_id: False,
        task_exists=lambda _task_id: False,
    )


def _data_error_repository() -> SimpleNamespace:
    def _raise_data_error(*_args: object, **_kwargs: object) -> None:
        message = "corrupt task payload"
        raise StorageDataError(message)

    return SimpleNamespace(
        initialize=lambda: None,
        save_task=lambda _task: None,
        get_task=lambda _task_id: _raise_data_error(),
        get_all_tasks=list,
        delete_task=lambda _task_id: _raise_data_error(),
        task_exists=lambda _task_id: False,
    )


def _in_memory_repository() -> SimpleNamespace:
    task = TaskModel(name="Sample", details="Details")

    return SimpleNamespace(
        task=task,
        initialize=lambda: None,
        save_task=lambda _updated_task: None,
        get_task=lambda _task_id: task if task.task_id == _task_id else None,
        get_all_tasks=lambda: [task],
        delete_task=lambda _task_id: task.task_id == _task_id,
        task_exists=lambda _task_id: task.task_id == _task_id,
    )


def test_get_task_raises_task_not_found() -> None:
    """Service should raise TaskNotFoundError when repository returns None."""
    service = TaskService(_not_found_repository())
    task_id = uuid4()

    with pytest.raises(TaskNotFoundError) as exc_info:
        service.get_task(task_id)

    assert exc_info.value.task_id == task_id


def test_delete_task_raises_task_not_found_when_not_removed() -> None:
    """Service should raise TaskNotFoundError when delete fails."""
    service = TaskService(_not_found_repository())
    task_id = uuid4()

    with pytest.raises(TaskNotFoundError) as exc_info:
        service.delete_task(task_id)

    assert exc_info.value.task_id == task_id


def test_storage_data_error_translates_to_validation_error_on_get() -> None:
    """Storage data issues should surface as TaskValidationError."""
    service = TaskService(_data_error_repository())

    with pytest.raises(TaskValidationError) as exc_info:
        service.get_task(uuid4())

    assert "invalid" in str(exc_info.value).lower()


def test_storage_data_error_translates_to_validation_error_on_delete() -> None:
    """Storage data issues should surface as TaskValidationError for delete."""
    service = TaskService(_data_error_repository())

    with pytest.raises(TaskValidationError):
        service.delete_task(uuid4())


def test_successful_operations_do_not_raise() -> None:
    """Service should return values for successful operations."""
    repository = _in_memory_repository()
    service = TaskService(repository)

    task = service.get_task(repository.task.task_id)
    assert task is repository.task

    assert service.delete_task(repository.task.task_id) is True

