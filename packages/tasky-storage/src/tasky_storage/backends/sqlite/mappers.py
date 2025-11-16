"""Mappers for converting between TaskModel and SQLite storage representations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tasky_tasks.models import TaskModel

from tasky_storage.shared import (
    snapshot_to_task_model as shared_snapshot_to_task_model,
)
from tasky_storage.shared import (
    task_model_to_snapshot as shared_task_model_to_snapshot,
)

if TYPE_CHECKING:
    import sqlite3


def task_model_to_snapshot(task: TaskModel) -> dict[str, Any]:
    """Serialize a TaskModel into a storage-friendly dictionary snapshot.

    This uses mode='json' to ensure all values are properly serialized:
    - Enums are converted to their string values
    - Datetimes are converted to ISO format strings
    - UUIDs are converted to strings

    Parameters
    ----------
    task:
        The task model to serialize

    Returns
    -------
    dict[str, Any]:
        Dictionary with JSON-serializable values (strings, ints, etc.)

    """
    return shared_task_model_to_snapshot(task, mode="json")


def snapshot_to_task_model(snapshot: dict[str, Any]) -> TaskModel:
    """Deserialize a stored task snapshot into a TaskModel.

    Parameters
    ----------
    snapshot:
        Dictionary representation from storage

    Returns
    -------
    TaskModel:
        Validated task model instance

    """
    return shared_snapshot_to_task_model(snapshot)


def row_to_snapshot(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row to a task snapshot dictionary.

    Parameters
    ----------
    row:
        SQLite row object from query result

    Returns
    -------
    dict[str, Any]:
        Dictionary representation of the task

    """
    return dict(row)
