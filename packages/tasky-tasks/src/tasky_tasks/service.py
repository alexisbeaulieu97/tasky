"""Service layer for task management operations.

The service boundary translates storage-level failures into domain exceptions so
callers receive consistent error semantics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tasky_hooks.events import (
    BaseEvent,
    TaskCancelledEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskDeletedEvent,
    TaskReopenedEvent,
    TaskSnapshot,
    TaskUpdatedEvent,
)
from tasky_logging import get_logger  # type: ignore[import-untyped]

from tasky_tasks.exceptions import TaskNotFoundError, TaskValidationError
from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus
from tasky_tasks.protocols import StorageErrorProtocol

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from tasky_hooks.dispatcher import HookDispatcher

    from tasky_tasks.ports import TaskRepository


logger: logging.Logger = get_logger("tasks.service")  # type: ignore[no-untyped-call]


class TaskService:
    """Service for managing tasks."""

    def __init__(
        self,
        repository: TaskRepository,
        dispatcher: HookDispatcher | None = None,
    ) -> None:
        self.repository = repository
        self.dispatcher = dispatcher

    def _create_snapshot(self, task: TaskModel) -> TaskSnapshot:
        """Create a snapshot of the task for events."""
        # Convert enum to string value for serialization
        data = task.model_dump(mode="json")
        return TaskSnapshot(**data)

    def _emit(self, event: BaseEvent) -> None:
        """Emit an event if a dispatcher is configured."""
        if self.dispatcher:
            self.dispatcher.dispatch(event)

    def create_task(self, name: str, details: str) -> TaskModel:
        """Create a new task."""
        task = TaskModel(name=name, details=details)
        self.repository.save_task(task)
        logger.info("Task created: id=%s, name=%s", task.task_id, task.name)

        self._emit(
            TaskCreatedEvent(
                task_id=task.task_id,
                task_snapshot=self._create_snapshot(task),
                project_root="",  # TODO: Inject project root
            )
        )
        return task

    def get_task(self, task_id: UUID) -> TaskModel:
        """Get a task by ID.

        Raises
        ------
        TaskNotFoundError
            Raised when the requested task does not exist.
        TaskValidationError
            Raised when stored task data is invalid.
        StorageError
            Propagated when lower layers encounter infrastructure failures.

        """
        logger.debug("Getting task: id=%s", task_id)
        try:
            task = self.repository.get_task(task_id)
        except Exception as exc:
            # Catch storage errors that implement the StorageErrorProtocol
            if isinstance(exc, StorageErrorProtocol):
                message = f"Stored data for task '{task_id}' is invalid."
                raise TaskValidationError(message) from exc
            raise

        if task is None:
            raise TaskNotFoundError(task_id)

        return task

    def get_all_tasks(self) -> list[TaskModel]:
        """Get all tasks."""
        tasks = self.repository.get_all_tasks()
        logger.debug("Retrieved all tasks: count=%d", len(tasks))
        return tasks

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Get tasks filtered by status.

        Parameters
        ----------
        status:
            The task status to filter by.

        Returns
        -------
        list[TaskModel]:
            List of tasks matching the specified status.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        logger.debug("Getting tasks by status: status=%s", status.value)
        try:
            tasks = self.repository.get_tasks_by_status(status)
        except Exception as exc:
            # Catch storage errors that implement the StorageErrorProtocol
            if isinstance(exc, StorageErrorProtocol):
                message = "Unable to retrieve tasks due to corrupted data."
                raise TaskValidationError(message) from exc
            raise

        logger.debug("Retrieved tasks by status: status=%s, count=%d", status.value, len(tasks))
        return tasks

    def get_pending_tasks(self) -> list[TaskModel]:
        """Get all pending tasks.

        Returns
        -------
        list[TaskModel]:
            List of tasks with pending status.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        return self.get_tasks_by_status(TaskStatus.PENDING)

    def get_completed_tasks(self) -> list[TaskModel]:
        """Get all completed tasks.

        Returns
        -------
        list[TaskModel]:
            List of tasks with completed status.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        return self.get_tasks_by_status(TaskStatus.COMPLETED)

    def get_cancelled_tasks(self) -> list[TaskModel]:
        """Get all cancelled tasks.

        Returns
        -------
        list[TaskModel]:
            List of tasks with cancelled status.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        return self.get_tasks_by_status(TaskStatus.CANCELLED)

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Find tasks matching the specified filter criteria.

        All criteria in the filter are combined using AND logic—tasks must
        match all specified criteria to be included in the results.

        Parameters
        ----------
        task_filter:
            The filter criteria to apply. None values in filter fields
            indicate no filtering on that dimension.

        Returns
        -------
        list[TaskModel]:
            List of tasks matching all specified filter criteria.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        logger.debug("Finding tasks with filter: %s", task_filter)
        try:
            tasks = self.repository.find_tasks(task_filter)
        except Exception as exc:
            # Catch storage errors that implement the StorageErrorProtocol
            if isinstance(exc, StorageErrorProtocol):
                message = "Unable to retrieve tasks due to corrupted data."
                raise TaskValidationError(message) from exc
            raise

        logger.debug("Found tasks: count=%d", len(tasks))
        return tasks

    def get_tasks_by_date_range(
        self,
        created_after: datetime,
        created_before: datetime,
    ) -> list[TaskModel]:
        """Get tasks created within a specific date range.

        Parameters
        ----------
        created_after:
            Include tasks created on or after this datetime (inclusive).
        created_before:
            Include tasks created before this datetime (exclusive).

        Returns
        -------
        list[TaskModel]:
            List of tasks created within the specified date range.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        task_filter = TaskFilter(
            created_after=created_after,
            created_before=created_before,
        )
        return self.find_tasks(task_filter)

    def search_tasks(self, text: str) -> list[TaskModel]:
        """Search tasks by name or details (case-insensitive).

        Parameters
        ----------
        text:
            The text to search for in task names and details.

        Returns
        -------
        list[TaskModel]:
            List of tasks containing the search text.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        task_filter = TaskFilter(name_contains=text)
        return self.find_tasks(task_filter)

    def get_pending_tasks_since(self, date: datetime) -> list[TaskModel]:
        """Get pending tasks created on or after a specific date.

        Parameters
        ----------
        date:
            Include tasks created on or after this datetime (inclusive).

        Returns
        -------
        list[TaskModel]:
            List of pending tasks created on or after the specified date.

        Raises
        ------
        TaskValidationError:
            Raised when stored task data is invalid.
        StorageError:
            Propagated when lower layers encounter infrastructure failures.

        """
        task_filter = TaskFilter(
            statuses=[TaskStatus.PENDING],
            created_after=date,
        )
        return self.find_tasks(task_filter)

    def update_task(self, task: TaskModel) -> None:
        """Update an existing task."""
        # Try to get the old state for the event
        old_snapshot = None
        try:
            old_task = self.repository.get_task(task.task_id)
            if old_task:
                old_snapshot = self._create_snapshot(old_task)
        except Exception:
            logger.warning("Failed to retrieve old task state for update event")

        task.mark_updated()
        self.repository.save_task(task)
        logger.info("Task updated: id=%s", task.task_id)

        if old_snapshot:
            new_snapshot = self._create_snapshot(task)
            # Calculate updated fields
            updated_fields = []
            old_data = old_snapshot.model_dump()
            new_data = new_snapshot.model_dump()
            for key, value in new_data.items():
                if key in old_data and old_data[key] != value:
                    updated_fields.append(key)

            self._emit(
                TaskUpdatedEvent(
                    task_id=task.task_id,
                    old_snapshot=old_snapshot,
                    new_snapshot=new_snapshot,
                    updated_fields=updated_fields,
                )
            )

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID.

        Raises
        ------
        TaskNotFoundError
            Raised when the task to delete does not exist.
        TaskValidationError
            Raised when stored task data is invalid.
        StorageError
            Propagated when lower layers encounter infrastructure failures.

        Returns
        -------
        bool
            ``True`` when the task was removed successfully.

        """
        # Get task before deletion for snapshot
        task_snapshot = None
        try:
            task = self.repository.get_task(task_id)
            if task:
                task_snapshot = self._create_snapshot(task)
        except Exception:
            pass

        try:
            removed = self.repository.delete_task(task_id)
        except Exception as exc:
            # Catch storage errors that implement the StorageErrorProtocol
            if isinstance(exc, StorageErrorProtocol):
                message = f"Stored data for task '{task_id}' is invalid."
                raise TaskValidationError(message) from exc
            raise

        if not removed:
            raise TaskNotFoundError(task_id)

        logger.info("Deleted task: id=%s", task_id)

        if task_snapshot:
            self._emit(
                TaskDeletedEvent(
                    task_id=task_id,
                    task_snapshot=task_snapshot,
                )
            )

        return True

    def task_exists(self, task_id: UUID) -> bool:
        """Check if a task exists."""
        logger.debug("Checking task existence: id=%s", task_id)
        return self.repository.task_exists(task_id)

    def complete_task(self, task_id: UUID) -> TaskModel:
        """Mark a task as completed.

        Fetches the task, transitions it to completed status, and persists
        the change.

        Parameters
        ----------
        task_id:
            The ID of the task to complete.

        Returns
        -------
        TaskModel:
            The updated task model with completed status.

        Raises
        ------
        TaskNotFoundError:
            Raised when the task does not exist.
        InvalidStateTransitionError:
            Raised when the task cannot be completed from its current status.
        TaskValidationError:
            Raised when stored task data is invalid.

        """
        task = self.get_task(task_id)
        task.complete()
        self.repository.save_task(task)
        logger.info("Task completed: id=%s, name=%s", task.task_id, task.name)

        self._emit(
            TaskCompletedEvent(
                task_id=task.task_id,
                task_snapshot=self._create_snapshot(task),
                completion_timestamp=task.updated_at,
            )
        )
        return task

    def cancel_task(self, task_id: UUID) -> TaskModel:
        """Mark a task as cancelled.

        Fetches the task, transitions it to cancelled status, and persists
        the change.

        Parameters
        ----------
        task_id:
            The ID of the task to cancel.

        Returns
        -------
        TaskModel:
            The updated task model with cancelled status.

        Raises
        ------
        TaskNotFoundError:
            Raised when the task does not exist.
        InvalidStateTransitionError:
            Raised when the task cannot be cancelled from its current status.
        TaskValidationError:
            Raised when stored task data is invalid.

        """
        task = self.get_task(task_id)
        previous_status = task.status.value
        task.cancel()
        self.repository.save_task(task)
        logger.info("Task cancelled: id=%s, name=%s", task.task_id, task.name)

        self._emit(
            TaskCancelledEvent(
                task_id=task.task_id,
                task_snapshot=self._create_snapshot(task),
                previous_status=previous_status,
            )
        )
        return task

    def reopen_task(self, task_id: UUID) -> TaskModel:
        """Reopen a completed or cancelled task.

        Fetches the task, transitions it back to pending status, and persists
        the change.

        Parameters
        ----------
        task_id:
            The ID of the task to reopen.

        Returns
        -------
        TaskModel:
            The updated task model with pending status.

        Raises
        ------
        TaskNotFoundError:
            Raised when the task does not exist.
        InvalidStateTransitionError:
            Raised when the task cannot be reopened from its current status.
        TaskValidationError:
            Raised when stored task data is invalid.

        """
        task = self.get_task(task_id)
        previous_status = task.status.value
        task.reopen()
        self.repository.save_task(task)
        logger.info("Task reopened: id=%s, name=%s", task.task_id, task.name)

        self._emit(
            TaskReopenedEvent(
                task_id=task.task_id,
                task_snapshot=self._create_snapshot(task),
                previous_status=previous_status,
                new_status=task.status.value,
            )
        )
        return task
