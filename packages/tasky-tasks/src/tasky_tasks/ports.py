"""Repository port definitions for task persistence operations."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from tasky_tasks.models import TaskModel, TaskStatus


class TaskRepository(Protocol):
    """Repository interface for task persistence operations."""

    def initialize(self) -> None:
        """Initialize the storage with default state if needed."""
        ...

    def save_task(self, task: TaskModel) -> None:
        """Persist a task."""
        ...

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Retrieve a task by ID."""
        ...

    def get_all_tasks(self) -> list[TaskModel]:
        """Retrieve all tasks."""
        ...

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Retrieve tasks filtered by status.

        Parameters
        ----------
        status:
            The task status to filter by.

        Returns
        -------
        list[TaskModel]:
            List of tasks matching the specified status.

        """
        ...

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID. Return True when a record was removed."""
        ...

    def task_exists(self, task_id: UUID) -> bool:
        """Determine whether a task exists in storage."""
        ...
