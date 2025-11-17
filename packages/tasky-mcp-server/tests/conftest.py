"""Shared test fixtures for tasky-mcp-server tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from tasky_settings.factory import create_task_service

if TYPE_CHECKING:
    from tasky_tasks.models import TaskModel
    from tasky_tasks.service import TaskService


class InMemoryTaskRepository:
    """In-memory task repository for testing."""

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._tasks: dict[UUID, TaskModel] = {}

    @classmethod
    def from_tasks(cls, tasks: list[TaskModel]) -> InMemoryTaskRepository:
        """Create repository pre-populated with tasks."""
        repo = cls()
        for task in tasks:
            repo._tasks[task.task_id] = task
        return repo

    def create_task(self, task: TaskModel) -> TaskModel:
        """Create a task."""
        self._tasks[task.task_id] = task
        return task

    def save_task(self, task: TaskModel) -> None:
        """Save a task (create or update)."""
        self._tasks[task.task_id] = task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        """Get all tasks."""
        return list(self._tasks.values())

    def update_task(self, task: TaskModel) -> TaskModel:
        """Update a task."""
        self._tasks[task.task_id] = task
        return task

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def mock_task_repository() -> InMemoryTaskRepository:
    """Create a mock task repository."""
    return InMemoryTaskRepository()


@pytest.fixture
def task_service(tmp_path: Path) -> TaskService:
    """Create a TaskService with JSON backend."""
    # Initialize a .tasky directory
    tasky_dir = tmp_path / ".tasky"
    tasky_dir.mkdir()

    return create_task_service(project_root=tmp_path)
