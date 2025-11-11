"""Service layer for task management operations."""

from typing import TYPE_CHECKING

from tasky_tasks.models import TaskModel

if TYPE_CHECKING:
    from uuid import UUID

    from tasky_tasks.ports import TaskRepository


class TaskService:
    """Service for managing tasks."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, name: str, details: str) -> TaskModel:
        """Create a new task."""
        task = TaskModel(name=name, details=details)
        self.repository.save_task(task)
        return task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Get a task by ID."""
        return self.repository.get_task(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        """Get all tasks."""
        return self.repository.get_all_tasks()

    def update_task(self, task: TaskModel) -> None:
        """Update an existing task."""
        self.repository.save_task(task)

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID."""
        return self.repository.delete_task(task_id)

    def task_exists(self, task_id: UUID) -> bool:
        """Check if a task exists."""
        return self.repository.task_exists(task_id)
