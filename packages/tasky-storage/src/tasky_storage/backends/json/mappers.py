"""Mappers for converting between TaskModel and storage snapshots."""

from typing import Any

from tasky_tasks.models import TaskModel

from tasky_storage.utils import (
    snapshot_to_task_model as shared_snapshot_to_task_model,
)
from tasky_storage.utils import (
    task_model_to_snapshot as shared_task_model_to_snapshot,
)


def task_model_to_snapshot(task: TaskModel) -> dict[str, Any]:
    """Serialize a TaskModel into a storage-friendly dictionary snapshot.

    Uses mode='json' to ensure consistent serialization across backends.
    """
    return shared_task_model_to_snapshot(task, mode="json")


def snapshot_to_task_model(snapshot: dict[str, Any]) -> TaskModel:
    """Deserialize a stored task snapshot into a TaskModel."""
    return shared_snapshot_to_task_model(snapshot)
