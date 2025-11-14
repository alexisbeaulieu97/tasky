"""JSON-based task repository implementation for the Tasky application.

This module defines the JsonTaskRepository class, which implements the TaskRepository
protocol using JSON file storage. It handles persistence, retrieval, and management of
TaskModel instances through a JsonStorage backend and TaskDocument structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError
from tasky_logging import get_logger

from tasky_storage.backends.json.document import TaskDocument
from tasky_storage.backends.json.mappers import (
    snapshot_to_task_model,
    task_model_to_snapshot,
)
from tasky_storage.backends.json.storage import JsonStorage
from tasky_storage.errors import StorageDataError

if TYPE_CHECKING:
    from pathlib import Path
    from uuid import UUID

    from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


logger = get_logger("storage.json.repository")


class JsonTaskRepository(BaseModel):
    """JSON-based task repository implementation."""

    storage: JsonStorage

    def initialize(self) -> None:
        """Initialize storage with empty task document if needed."""
        template = TaskDocument.create_empty().model_dump()
        self.storage.initialize(template)

    def save_task(self, task: TaskModel) -> None:
        """Persist a task snapshot to storage."""
        logger.debug("Saving task: id=%s", task.task_id)
        document = self._load_document_optional()
        if document is None:
            self.initialize()
            document = TaskDocument.create_empty()

        snapshot = task_model_to_snapshot(task)
        document.add_task(str(task.task_id), snapshot)
        self.storage.save(document.model_dump())

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Retrieve a task by ID."""
        logger.debug("Getting task: id=%s", task_id)
        document = self._load_document_optional()
        if document is None:
            return None

        snapshot = document.get_task(str(task_id))
        if snapshot is None:
            return None

        return self._snapshot_to_task(snapshot)

    def get_all_tasks(self) -> list[TaskModel]:
        """Retrieve all tasks."""
        logger.debug("Getting all tasks")
        document = self._load_document_optional()
        if document is None:
            return []

        tasks = [self._snapshot_to_task(snapshot) for snapshot in document.list_tasks()]
        logger.debug("Retrieved all tasks: count=%d", len(tasks))
        return tasks

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
        logger.debug("Getting tasks by status: status=%s", status.value)
        document = self._load_document_optional()
        if document is None:
            return []

        tasks = [
            self._snapshot_to_task(snapshot)
            for snapshot in document.list_tasks()
            if snapshot.get("status") == status.value
        ]
        logger.debug("Retrieved tasks by status: status=%s, count=%d", status.value, len(tasks))
        return tasks

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Retrieve tasks matching the specified filter criteria.

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

        """
        logger.debug("Finding tasks with filter: %s", task_filter)
        document = self._load_document_optional()
        if document is None:
            return []

        # Convert snapshots to TaskModel instances and filter using filter.matches()
        tasks = [
            task
            for snapshot in document.list_tasks()
            if (task := self._snapshot_to_task(snapshot)) and task_filter.matches(task)
        ]
        logger.debug("Found tasks: count=%d", len(tasks))
        return tasks

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID."""
        logger.debug("Deleting task: id=%s", task_id)
        document = self._load_document_optional()
        if document is None:
            return False

        removed = document.remove_task(str(task_id))
        if removed:
            self.storage.save(document.model_dump())
            logger.debug("Task deleted: id=%s", task_id)

        return removed

    def task_exists(self, task_id: UUID) -> bool:
        """Check if a task exists."""
        document = self._load_document_optional()
        if document is None:
            return False

        return str(task_id) in document.tasks

    @classmethod
    def from_path(cls, path: Path) -> JsonTaskRepository:
        """Create a repository from a file path."""
        storage = JsonStorage(path=path)
        return cls(storage=storage)

    def _load_document_optional(self) -> TaskDocument | None:
        try:
            return self._load_document()
        except StorageDataError as exc:
            if self._originated_from_missing_file(exc):
                return None
            logger.warning("Failed to load task document: %s", exc)
            raise

    def _load_document(self) -> TaskDocument:
        data = self.storage.load()
        try:
            return TaskDocument.model_validate(data)
        except ValidationError as exc:
            raise StorageDataError(exc) from exc

    @staticmethod
    def _snapshot_to_task(snapshot: dict[str, Any]) -> TaskModel:
        try:
            return snapshot_to_task_model(snapshot)
        except ValidationError as exc:
            raise StorageDataError(exc) from exc

    @staticmethod
    def _originated_from_missing_file(error: StorageDataError) -> bool:
        cause = error.__cause__ or error.__context__
        return isinstance(cause, FileNotFoundError)
