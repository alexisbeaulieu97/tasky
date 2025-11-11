"""Tests for the task domain exception hierarchy."""

from __future__ import annotations

from uuid import uuid4

from tasky_tasks.exceptions import (
    InvalidStateTransitionError,
    TaskDomainError,
    TaskNotFoundError,
    TaskValidationError,
)


def test_task_domain_error_supports_message_and_context() -> None:
    """Base exception should store message and context."""
    error = TaskDomainError("Something happened", operation="create")

    assert str(error) == "Something happened"
    assert error.context == {"operation": "create"}
    assert "operation='create'" in repr(error)


def test_task_not_found_error_includes_task_id_and_message() -> None:
    """TaskNotFoundError should expose task_id and readable message."""
    task_id = uuid4()
    error = TaskNotFoundError(task_id)

    assert error.task_id == task_id
    assert str(error) == f"Task '{task_id}' was not found."
    assert error.context == {"task_id": str(task_id)}


def test_task_not_found_error_accepts_custom_message() -> None:
    """TaskNotFoundError should accept a custom message."""
    task_id = uuid4()
    error = TaskNotFoundError(task_id, message="Custom message")

    assert str(error) == "Custom message"
    assert error.context["task_id"] == str(task_id)


def test_task_validation_error_captures_field_context() -> None:
    """TaskValidationError should expose failing field when provided."""
    error = TaskValidationError("Name cannot be empty", field="name")

    assert error.field == "name"
    assert error.context == {"field": "name"}
    assert "Name cannot be empty" in str(error)


def test_task_validation_error_uses_default_message() -> None:
    """TaskValidationError should have a sensible default message."""
    error = TaskValidationError()

    assert str(error) == "Task validation failed."
    assert error.context == {}


def test_invalid_state_transition_error_includes_context() -> None:
    """InvalidStateTransitionError should capture transition details."""
    task_id = uuid4()
    error = InvalidStateTransitionError(task_id, from_status="completed", to_status="cancelled")

    assert error.task_id == task_id
    assert error.from_status == "completed"
    assert error.to_status == "cancelled"
    assert "Cannot transition task" in str(error)
    assert error.context == {
        "task_id": str(task_id),
        "from_status": "completed",
        "to_status": "cancelled",
    }


def test_exception_hierarchy_relationships() -> None:
    """All domain exceptions should inherit from TaskDomainError."""
    assert issubclass(TaskNotFoundError, TaskDomainError)
    assert issubclass(TaskValidationError, TaskDomainError)
    assert issubclass(InvalidStateTransitionError, TaskDomainError)

    for exc in (
        TaskNotFoundError(uuid4()),
        TaskValidationError("msg"),
        InvalidStateTransitionError(uuid4(), "pending", "completed"),
    ):
        assert isinstance(exc, TaskDomainError)

