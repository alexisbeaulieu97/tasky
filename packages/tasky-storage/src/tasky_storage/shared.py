"""Shared utilities for task storage backends.

This module provides common functionality used across different storage implementations,
reducing code duplication and ensuring consistent behavior.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from tasky_tasks.models import TaskModel

from tasky_storage.errors import StorageDataError


def snapshot_to_task_model(snapshot: dict[str, Any]) -> TaskModel:
    """Convert a snapshot dictionary to a TaskModel, handling validation errors.

    This function provides consistent error handling across all storage backends.
    It deserializes a stored task snapshot (dictionary) into a validated TaskModel
    instance, wrapping any validation errors in StorageDataError.

    Parameters
    ----------
    snapshot:
        Dictionary representation of a task from storage. Expected to contain
        keys matching TaskModel fields: task_id, name, details, status,
        created_at, updated_at. Date strings should be in ISO format.

    Returns
    -------
    TaskModel:
        Validated task model instance

    Raises
    ------
    StorageDataError:
        If snapshot validation fails (e.g., missing required fields,
        invalid field types, malformed datetime strings)

    """
    try:
        return TaskModel.model_validate(snapshot)
    except ValidationError as exc:
        raise StorageDataError(exc) from exc


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
