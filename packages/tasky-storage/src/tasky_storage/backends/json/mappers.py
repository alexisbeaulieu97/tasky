from typing import Any

from tasky_tasks.models import TaskModel


def task_model_to_snapshot(task: TaskModel) -> dict[str, Any]:
    """Serialize a TaskModel into a storage-friendly dictionary snapshot."""
    return task.model_dump()


def snapshot_to_task_model(snapshot: dict[str, Any]) -> TaskModel:
    """Deserialize a stored task snapshot into a TaskModel."""
    return TaskModel.model_validate(snapshot)
