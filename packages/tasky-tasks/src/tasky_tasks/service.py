"""Service layer for task management operations.

The service boundary translates storage-level failures into domain exceptions so
callers receive consistent error semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tasky_tasks.exceptions import TaskNotFoundError, TaskValidationError
from tasky_tasks.models import TaskModel

if TYPE_CHECKING:
    from uuid import UUID

    from tasky_tasks.ports import TaskRepository

try:  # pragma: no cover - optional dependency at runtime
    from tasky_storage.errors import StorageDataError
except ModuleNotFoundError:  # pragma: no cover - fallback when storage is absent

    class StorageDataError(Exception):
        """Fallback storage data error used when storage package is unavailable."""


class TaskService:
    """Service for managing tasks."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, name: str, details: str) -> TaskModel:
        """Create a new task."""
        task = TaskModel(name=name, details=details)
        self.repository.save_task(task)
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
        try:
            task = self.repository.get_task(task_id)
        except StorageDataError as exc:
            message = f"Stored data for task '{task_id}' is invalid."
            raise TaskValidationError(message) from exc

        if task is None:
            raise TaskNotFoundError(task_id)

        return task

    def get_all_tasks(self) -> list[TaskModel]:
        """Get all tasks."""
        return self.repository.get_all_tasks()

    def update_task(self, task: TaskModel) -> None:
        """Update an existing task."""
        task.mark_updated()
        self.repository.save_task(task)

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
        try:
            removed = self.repository.delete_task(task_id)
        except StorageDataError as exc:
            message = f"Stored data for task '{task_id}' is invalid."
            raise TaskValidationError(message) from exc

        if not removed:
            raise TaskNotFoundError(task_id)

        return True

    def task_exists(self, task_id: UUID) -> bool:
        """Check if a task exists."""
        return self.repository.task_exists(task_id)
