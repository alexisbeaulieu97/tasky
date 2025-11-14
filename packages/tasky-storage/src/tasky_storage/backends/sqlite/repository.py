"""SQLite-based task repository implementation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import ValidationError
from tasky_logging import get_logger

from tasky_storage.backends.sqlite.connection import get_connection
from tasky_storage.backends.sqlite.mappers import (
    row_to_snapshot,
    snapshot_to_task_model,
    task_model_to_snapshot,
)
from tasky_storage.backends.sqlite.schema import create_schema, validate_schema
from tasky_storage.errors import StorageDataError, StorageError

if TYPE_CHECKING:
    from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


logger = get_logger("storage.sqlite.repository")


class SqliteTaskRepository:
    """SQLite-based task repository implementation."""

    def __init__(self, path: Path) -> None:
        """Initialize the repository.

        Parameters
        ----------
        path:
            Path to the SQLite database file

        """
        self.path = path

    def initialize(self) -> None:
        """Initialize storage with schema if needed."""
        logger.debug("Initializing SQLite database: path=%s", self.path)

        # Create parent directory if needed
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Create schema
        with get_connection(self.path) as conn:
            create_schema(conn)

            # Validate schema
            if not validate_schema(conn):
                msg = f"Database integrity check failed: {self.path}"
                raise StorageDataError(msg)

        logger.debug("Database initialized successfully")

    def save_task(self, task: TaskModel) -> None:
        """Persist a task snapshot to storage.

        Parameters
        ----------
        task:
            Task model to persist

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Saving task: id=%s", task.task_id)

        # Use mode='json' to get properly serialized values
        # (enums as strings, datetimes as ISO format)
        snapshot = task_model_to_snapshot(task)

        try:
            # Use connection as context manager for automatic rollback on error
            with get_connection(self.path) as conn, conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO tasks (
                        task_id, name, details, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot["task_id"],
                        snapshot["name"],
                        snapshot["details"],
                        snapshot["status"],
                        snapshot["created_at"],
                        snapshot["updated_at"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            msg = f"Database integrity error saving task {task.task_id}: {exc}"
            raise StorageDataError(msg) from exc
        except sqlite3.OperationalError as exc:
            msg = f"Database locked or inaccessible: {exc}"
            raise StorageError(msg) from exc
        except sqlite3.Error as exc:
            msg = f"Database error saving task {task.task_id}: {exc}"
            raise StorageError(msg) from exc

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Retrieve a task by ID.

        Parameters
        ----------
        task_id:
            Task identifier

        Returns
        -------
        TaskModel | None:
            Task model if found, None otherwise

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Getting task: id=%s", task_id)

        try:
            with get_connection(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (str(task_id),))
                row = cursor.fetchone()

                if row is None:
                    return None

                # Note: row_to_snapshot returns dict with ISO string datetimes,
                # _snapshot_to_task converts them back to datetime objects
                snapshot = row_to_snapshot(row)
                return self._snapshot_to_task(snapshot)
        except sqlite3.Error as exc:
            msg = f"Database error retrieving task {task_id}: {exc}"
            raise StorageError(msg) from exc

    def get_all_tasks(self) -> list[TaskModel]:
        """Retrieve all tasks.

        Returns
        -------
        list[TaskModel]:
            List of all tasks

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Getting all tasks")

        try:
            with get_connection(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                rows = cursor.fetchall()

                tasks = [self._snapshot_to_task(row_to_snapshot(row)) for row in rows]
                logger.debug("Retrieved all tasks: count=%d", len(tasks))
                return tasks
        except sqlite3.Error as exc:
            msg = f"Database error retrieving all tasks: {exc}"
            raise StorageError(msg) from exc

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Retrieve tasks filtered by status.

        Parameters
        ----------
        status:
            The task status to filter by

        Returns
        -------
        list[TaskModel]:
            List of tasks matching the specified status

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Getting tasks by status: status=%s", status.value)

        try:
            with get_connection(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                    (status.value,),
                )
                rows = cursor.fetchall()

                tasks = [self._snapshot_to_task(row_to_snapshot(row)) for row in rows]
                logger.debug(
                    "Retrieved tasks by status: status=%s, count=%d",
                    status.value,
                    len(tasks),
                )
                return tasks
        except sqlite3.Error as exc:
            msg = f"Database error filtering tasks by status {status.value}: {exc}"
            raise StorageError(msg) from exc

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

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Finding tasks with filter: %s", task_filter)

        # Build SQL query with WHERE clauses for specified criteria
        where_clauses = []
        params = []

        # Add status filter
        self._add_status_filter(task_filter, where_clauses, params)
        if not where_clauses and task_filter.statuses is not None:
            # Empty statuses list means no results
            return []

        # Add date range filters
        self._add_date_filters(task_filter, where_clauses, params)

        # Add text search filter
        self._add_text_filter(task_filter, where_clauses, params)

        # Build and execute query
        query = self._build_query(where_clauses)
        return self._execute_find_query(query, params)

    def _add_status_filter(
        self,
        task_filter: TaskFilter,
        where_clauses: list[str],
        params: list[Any],
    ) -> None:
        """Add status filter to WHERE clauses."""
        if task_filter.statuses is not None and task_filter.statuses:
            placeholders = ",".join("?" * len(task_filter.statuses))
            where_clauses.append(f"status IN ({placeholders})")
            params.extend(status.value for status in task_filter.statuses)

    def _add_date_filters(
        self,
        task_filter: TaskFilter,
        where_clauses: list[str],
        params: list[Any],
    ) -> None:
        """Add date range filters to WHERE clauses."""
        if task_filter.created_after is not None:
            where_clauses.append("created_at >= ?")
            params.append(task_filter.created_after.isoformat())

        if task_filter.created_before is not None:
            where_clauses.append("created_at < ?")
            params.append(task_filter.created_before.isoformat())

    def _add_text_filter(
        self,
        task_filter: TaskFilter,
        where_clauses: list[str],
        params: list[Any],
    ) -> None:
        """Add text search filter to WHERE clauses."""
        if task_filter.name_contains is not None:
            # Escape LIKE metacharacters to prevent wildcard interpretation
            # Users expect literal substring matching, not SQL wildcard behavior
            escaped_search = (
                task_filter.name_contains.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            # SQLite LIKE is case-insensitive by default for ASCII characters
            where_clauses.append("(name LIKE ? ESCAPE '\\' OR details LIKE ? ESCAPE '\\')")
            search_pattern = f"%{escaped_search}%"
            params.extend([search_pattern, search_pattern])

    def _build_query(self, where_clauses: list[str]) -> str:
        """Build SQL query string from WHERE clauses."""
        query = "SELECT * FROM tasks"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY created_at DESC"
        return query

    def _execute_find_query(self, query: str, params: list[Any]) -> list[TaskModel]:
        """Execute find query and convert rows to TaskModels."""
        try:
            with get_connection(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                tasks = [self._snapshot_to_task(row_to_snapshot(row)) for row in rows]
                logger.debug("Found tasks: count=%d", len(tasks))
                return tasks
        except sqlite3.Error as exc:
            msg = f"Database error finding tasks: {exc}"
            raise StorageError(msg) from exc

    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID.

        Parameters
        ----------
        task_id:
            Task identifier

        Returns
        -------
        bool:
            True if a record was removed, False otherwise

        Raises
        ------
        StorageError:
            If database operation fails

        """
        logger.debug("Deleting task: id=%s", task_id)

        try:
            # Use connection as context manager for automatic rollback on error
            with get_connection(self.path) as conn, conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE task_id = ?", (str(task_id),))

                removed = cursor.rowcount > 0
                if removed:
                    logger.debug("Task deleted: id=%s", task_id)

                return removed
        except sqlite3.Error as exc:
            msg = f"Database error deleting task {task_id}: {exc}"
            raise StorageError(msg) from exc

    def task_exists(self, task_id: UUID) -> bool:
        """Determine whether a task exists in storage.

        Parameters
        ----------
        task_id:
            Task identifier

        Returns
        -------
        bool:
            True if task exists, False otherwise

        Raises
        ------
        StorageError:
            If database operation fails

        """
        try:
            with get_connection(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE task_id = ? LIMIT 1", (str(task_id),))
                return cursor.fetchone() is not None
        except sqlite3.Error as exc:
            msg = f"Database error checking if task {task_id} exists: {exc}"
            raise StorageError(msg) from exc

    @classmethod
    def from_path(cls, path: Path) -> SqliteTaskRepository:
        """Create a repository from a file path.

        This factory method is suitable for backend registry.

        Parameters
        ----------
        path:
            Path to SQLite database file

        Returns
        -------
        SqliteTaskRepository:
            Configured repository instance

        """
        repository = cls(path=path)
        repository.initialize()
        return repository

    @staticmethod
    def _snapshot_to_task(snapshot: dict[str, Any]) -> TaskModel:
        """Convert a snapshot to a TaskModel, handling validation errors.

        Parameters
        ----------
        snapshot:
            Dictionary representation of a task

        Returns
        -------
        TaskModel:
            Validated task model

        Raises
        ------
        StorageDataError:
            If validation fails

        """
        try:
            return snapshot_to_task_model(snapshot)
        except ValidationError as exc:
            raise StorageDataError(exc) from exc
