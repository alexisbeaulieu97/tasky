from __future__ import annotations

from typing import Iterable, Protocol
from uuid import UUID

from tasky_models import Task


class TaskRepositoryError(Exception):
    """Raised when the task repository cannot fulfil a request."""


class TaskReader(Protocol):
    """Read-only task access boundary."""

    def list_tasks(self) -> list[Task]:
        """Return all persisted tasks."""
        ...


class TaskWriter(Protocol):
    """Write operations for task aggregates."""

    def upsert_task(self, task: Task) -> Task:
        """Insert or replace a task."""
        ...

    def delete_task(self, task_id: str | UUID) -> None:
        """Remove a task from persistent storage."""
        ...

    def replace_tasks(self, tasks: Iterable[Task]) -> None:
        """Overwrite storage with the provided sequence of tasks."""
        ...


class TaskRepository(TaskReader, TaskWriter, Protocol):
    """Convenience protocol for stores supporting both read/write operations."""
    ...
