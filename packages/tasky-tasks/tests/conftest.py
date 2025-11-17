"""Shared test fixtures for tasky-tasks package."""

from __future__ import annotations

import sys

if __name__ == "tests.conftest":
    # Ensure pytest registers this plugin under a stable, unique name.
    module = sys.modules[__name__]
    module.__name__ = "tasky_tasks.tests.conftest"
    sys.modules[module.__name__] = module

from uuid import UUID

from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


class InMemoryTaskRepository:
    """In-memory task repository for isolated unit testing.

    Implements the TaskRepository protocol without requiring actual storage.
    Supports both mutable operations (save/delete) and pre-population with test data.

    Attributes:
        tasks: Internal dict mapping UUID to TaskModel

    Example (mutable use):
        >>> repo = InMemoryTaskRepository()
        >>> service = TaskService(repo)
        >>> task = service.create_task("Test", "Details")
        >>> assert repo.task_exists(task.task_id)

    Example (pre-populated use):
        >>> task1 = TaskModel(name="Task 1", details="...")
        >>> task2 = TaskModel(name="Task 2", details="...")
        >>> repo = InMemoryTaskRepository.from_tasks([task1, task2])
        >>> assert len(repo.get_all_tasks()) == 2

    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self.tasks: dict[UUID, TaskModel] = {}

    @classmethod
    def from_tasks(cls, tasks: list[TaskModel]) -> InMemoryTaskRepository:
        """Create repository pre-populated with tasks.

        Args:
            tasks: List of tasks to include in repository

        Returns:
            Repository instance with tasks pre-loaded

        """
        repo = cls()
        for task in tasks:
            repo.tasks[task.task_id] = task
        return repo

    def initialize(self) -> None:
        """Reset repository to empty state.

        Useful for test cleanup between test cases.
        """
        self.tasks.clear()

    def save_task(self, task: TaskModel) -> None:
        """Persist a task to in-memory storage."""
        self.tasks[task.task_id] = task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Retrieve task by ID, or None if not found."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        """Return all stored tasks."""
        return list(self.tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Return tasks filtered by status."""
        return [task for task in self.tasks.values() if task.status == status]

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Return tasks matching filter criteria."""
        return [task for task in self.tasks.values() if task_filter.matches(task)]

    def delete_task(self, task_id: UUID) -> bool:
        """Remove task from storage, returning True if existed."""
        return self.tasks.pop(task_id, None) is not None

    def task_exists(self, task_id: UUID) -> bool:
        """Check if task exists in storage."""
        return task_id in self.tasks
