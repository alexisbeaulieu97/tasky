"""Tests for TaskService event emission."""

from unittest.mock import Mock

from tasky_hooks.dispatcher import HookDispatcher
from tasky_hooks.events import (
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeletedEvent,
    TaskReopenedEvent,
    TaskUpdatedEvent,
)
from tasky_tasks.service import TaskService

from .conftest import InMemoryTaskRepository


def test_create_task_emits_event() -> None:
    """Verify create_task emits TaskCreatedEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)

    task = service.create_task("Task", "Details")

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskCreatedEvent)
    assert event.task_id == task.task_id
    assert event.task_snapshot.name == "Task"


def test_update_task_emits_event() -> None:
    """Verify update_task emits TaskUpdatedEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)
    task = service.create_task("Task", "Details")
    dispatcher.reset_mock()

    # Use a copy to avoid modifying the in-memory repository reference
    updated_task = task.model_copy()
    updated_task.name = "Updated Task"
    service.update_task(updated_task)

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskUpdatedEvent)
    assert event.task_id == task.task_id
    assert event.old_snapshot.name == "Task"
    assert event.new_snapshot.name == "Updated Task"
    assert "name" in event.updated_fields
    assert "updated_at" in event.updated_fields


def test_complete_task_emits_event() -> None:
    """Verify complete_task emits TaskCompletedEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)
    task = service.create_task("Task", "Details")
    dispatcher.reset_mock()

    service.complete_task(task.task_id)

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskCompletedEvent)
    assert event.task_id == task.task_id
    assert event.task_snapshot.status == "completed"


def test_cancel_task_emits_event() -> None:
    """Verify cancel_task emits TaskCancelledEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)
    task = service.create_task("Task", "Details")
    dispatcher.reset_mock()

    service.cancel_task(task.task_id)

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskCancelledEvent)
    assert event.task_id == task.task_id
    assert event.previous_status == "pending"
    assert event.task_snapshot.status == "cancelled"


def test_reopen_task_emits_event() -> None:
    """Verify reopen_task emits TaskReopenedEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)
    task = service.create_task("Task", "Details")
    service.complete_task(task.task_id)
    dispatcher.reset_mock()

    service.reopen_task(task.task_id)

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskReopenedEvent)
    assert event.task_id == task.task_id
    assert event.previous_status == "completed"
    assert event.new_status == "pending"


def test_delete_task_emits_event() -> None:
    """Verify delete_task emits TaskDeletedEvent."""
    repository = InMemoryTaskRepository()
    dispatcher = Mock(spec=HookDispatcher)
    service = TaskService(repository, dispatcher=dispatcher)
    task = service.create_task("Task", "Details")
    dispatcher.reset_mock()

    service.delete_task(task.task_id)

    dispatcher.dispatch.assert_called_once()
    event = dispatcher.dispatch.call_args[0][0]
    assert isinstance(event, TaskDeletedEvent)
    assert event.task_id == task.task_id
    assert event.task_snapshot.name == "Task"
