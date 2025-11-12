"""Tests for task state machine transitions."""

from __future__ import annotations

import pytest
from tasky_tasks.exceptions import InvalidStateTransitionError
from tasky_tasks.models import TaskModel, TaskStatus


class TestStateTransitions:
    """Test valid and invalid state transitions for tasks."""

    def test_pending_to_completed(self) -> None:
        """Test transition from pending to completed."""
        task = TaskModel(name="Test Task", details="Details")
        original_updated = task.updated_at

        task.transition_to(TaskStatus.COMPLETED)

        assert task.status == TaskStatus.COMPLETED
        assert task.updated_at > original_updated

    def test_pending_to_cancelled(self) -> None:
        """Test transition from pending to cancelled."""
        task = TaskModel(name="Test Task", details="Details")
        original_updated = task.updated_at

        task.transition_to(TaskStatus.CANCELLED)

        assert task.status == TaskStatus.CANCELLED
        assert task.updated_at > original_updated

    def test_completed_to_pending(self) -> None:
        """Test transition from completed to pending (reopen)."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)
        original_updated = task.updated_at

        task.transition_to(TaskStatus.PENDING)

        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated

    def test_cancelled_to_pending(self) -> None:
        """Test transition from cancelled to pending (reopen)."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.CANCELLED)
        original_updated = task.updated_at

        task.transition_to(TaskStatus.PENDING)

        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated

    def test_invalid_completed_to_cancelled(self) -> None:
        """Test invalid transition from completed to cancelled."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            task.transition_to(TaskStatus.CANCELLED)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.COMPLETED
        assert exc_info.value.to_status == TaskStatus.CANCELLED
        assert task.status == TaskStatus.COMPLETED  # Status unchanged

    def test_invalid_cancelled_to_completed(self) -> None:
        """Test invalid transition from cancelled to completed."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.CANCELLED)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            task.transition_to(TaskStatus.COMPLETED)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.CANCELLED
        assert exc_info.value.to_status == TaskStatus.COMPLETED
        assert task.status == TaskStatus.CANCELLED  # Status unchanged

    def test_invalid_pending_to_pending(self) -> None:
        """Test invalid transition from pending to pending (no-op should fail)."""
        task = TaskModel(name="Test Task", details="Details")

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            task.transition_to(TaskStatus.PENDING)

        assert exc_info.value.task_id == task.task_id
        assert exc_info.value.from_status == TaskStatus.PENDING
        assert exc_info.value.to_status == TaskStatus.PENDING


class TestConvenienceMethods:
    """Test convenience methods for state transitions."""

    def test_complete_method(self) -> None:
        """Test complete() convenience method."""
        task = TaskModel(name="Test Task", details="Details")
        original_updated = task.updated_at

        task.complete()

        assert task.status == TaskStatus.COMPLETED
        assert task.updated_at > original_updated

    def test_cancel_method(self) -> None:
        """Test cancel() convenience method."""
        task = TaskModel(name="Test Task", details="Details")
        original_updated = task.updated_at

        task.cancel()

        assert task.status == TaskStatus.CANCELLED
        assert task.updated_at > original_updated

    def test_reopen_method_from_completed(self) -> None:
        """Test reopen() convenience method from completed status."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)
        original_updated = task.updated_at

        task.reopen()

        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated

    def test_reopen_method_from_cancelled(self) -> None:
        """Test reopen() convenience method from cancelled status."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.CANCELLED)
        original_updated = task.updated_at

        task.reopen()

        assert task.status == TaskStatus.PENDING
        assert task.updated_at > original_updated

    def test_complete_from_completed_raises_error(self) -> None:
        """Test that completing an already completed task raises an error."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError):
            task.complete()

    def test_cancel_from_cancelled_raises_error(self) -> None:
        """Test that canceling an already cancelled task raises an error."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.CANCELLED)

        with pytest.raises(InvalidStateTransitionError):
            task.cancel()

    def test_reopen_from_pending_raises_error(self) -> None:
        """Test that reopening a pending task raises an error."""
        task = TaskModel(name="Test Task", details="Details")

        with pytest.raises(InvalidStateTransitionError):
            task.reopen()


class TestErrorContext:
    """Test error context in InvalidStateTransitionError."""

    def test_error_message_includes_statuses(self) -> None:
        """Test that error message includes current and target status."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            task.transition_to(TaskStatus.CANCELLED)

        error_message = str(exc_info.value)
        assert "completed" in error_message.lower()
        assert "cancelled" in error_message.lower()
        assert str(task.task_id) in error_message

    def test_error_context_attributes(self) -> None:
        """Test that error has proper context attributes."""
        task = TaskModel(name="Test Task", details="Details", status=TaskStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            task.transition_to(TaskStatus.CANCELLED)

        error = exc_info.value
        assert error.task_id == task.task_id
        assert error.from_status == TaskStatus.COMPLETED
        assert error.to_status == TaskStatus.CANCELLED
        assert "from_status" in error.context
        assert "to_status" in error.context
        assert "task_id" in error.context
