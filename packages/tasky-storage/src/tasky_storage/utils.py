"""Shared utilities for task storage backends.

This module provides common functionality used across different storage implementations,
reducing code duplication and ensuring consistent behavior.

The utilities in this module are designed to be used by all storage backends
(JSON, SQLite, etc.) to ensure consistent serialization, deserialization, and
error handling across the entire storage layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from tasky_tasks.models import TaskModel

from tasky_storage.errors import SnapshotConversionError


def snapshot_to_task_model(snapshot: dict[str, Any]) -> TaskModel:
    """Convert a snapshot dictionary to a TaskModel, handling validation errors.

    This function provides consistent error handling across all storage backends.
    It deserializes a stored task snapshot (dictionary) into a validated TaskModel
    instance, wrapping any validation errors in SnapshotConversionError.

    This function consolidates logic from existing mappers in both JSON and SQLite
    backends to eliminate code duplication and ensure consistent behavior.

    Parameters
    ----------
    snapshot:
        Dictionary representation of a task from storage. Expected to contain
        keys matching TaskModel fields: task_id, name, details, status,
        created_at, updated_at. Date strings should be in ISO 8601 format.

    Returns
    -------
    TaskModel:
        Validated task model instance with all fields properly deserialized

    Raises
    ------
    SnapshotConversionError:
        If snapshot conversion fails due to:
        - Missing required fields (e.g., 'task_id', 'name')
        - Invalid field types (e.g., malformed UUID, invalid enum value)
        - Malformed datetime strings (must be ISO 8601 format)
        - Any other validation failure during TaskModel creation

        The original ValidationError is preserved in the __cause__ attribute
        for debugging purposes.

    Examples
    --------
    >>> snapshot = {
    ...     "task_id": "123e4567-e89b-12d3-a456-426614174000",
    ...     "name": "Fix bug",
    ...     "details": "Fix the login issue",
    ...     "status": "pending",
    ...     "created_at": "2025-11-16T10:00:00Z",
    ...     "updated_at": "2025-11-16T10:00:00Z"
    ... }
    >>> task = snapshot_to_task_model(snapshot)
    >>> task.name
    'Fix bug'

    """
    try:
        return TaskModel.model_validate(snapshot)
    except ValidationError as exc:
        # Extract the first error to provide an actionable message
        if exc.errors():
            first_error = exc.errors()[0]
            field = first_error.get("loc", ["unknown"])[0]
            error_type = first_error.get("type", "validation_error")
            msg = f"Failed to convert snapshot: {error_type} for field '{field}'"
        else:
            msg = "Failed to convert snapshot: validation failed"

        raise SnapshotConversionError(msg, cause=exc) from exc


def task_model_to_snapshot(task: TaskModel, *, mode: str = "json") -> dict[str, Any]:
    """Serialize a TaskModel into a storage-friendly dictionary snapshot.

    This function uses Pydantic's model_dump with mode='json' by default to ensure
    all values are properly serialized for storage:
    - Enums are converted to their string values
    - Datetimes are converted to ISO format strings
    - UUIDs are converted to strings

    Parameters
    ----------
    task:
        The task model to serialize
    mode:
        Pydantic serialization mode. Defaults to 'json' for storage-friendly output.

    Returns
    -------
    dict[str, Any]:
        Dictionary with serialized values suitable for storage

    """
    return task.model_dump(mode=mode)
