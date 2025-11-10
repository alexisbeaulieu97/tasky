from __future__ import annotations

import json
from typing import Any, Protocol, Sequence
from uuid import UUID

from tasky_models import Task


class TaskImportError(Exception):
    """Raised when bulk task import payloads are invalid."""


def load_tasks_from_json(payload: str) -> list[Task]:
    """
    Parse a JSON payload (list of tasks) into Task aggregates.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise TaskImportError("Import payload is not valid JSON.") from exc
    if not isinstance(data, list):
        raise TaskImportError("Import payload must be a JSON array of task objects.")
    return [_task_from_dict(entry) for entry in data]


def _task_from_dict(entry: Any) -> Task:
    if not isinstance(entry, dict):
        raise TaskImportError("Each task entry must be a JSON object.")
    task_kwargs = _extract_task_fields(entry)
    subtasks_payload = entry.get("subtasks") or []
    if not isinstance(subtasks_payload, list):
        raise TaskImportError("'subtasks' must be a list when provided.")
    children = [_task_from_dict(child) for child in subtasks_payload]
    return Task(subtasks=children, **task_kwargs)


def _extract_task_fields(entry: dict[str, Any]) -> dict[str, Any]:
    try:
        name = entry["name"]
        details = entry["details"]
    except KeyError as exc:
        raise TaskImportError("Task entries require 'name' and 'details' fields.") from exc

    task_kwargs: dict[str, Any] = {
        "name": name,
        "details": details,
        "completed": bool(entry.get("completed", False)),
    }
    task_id = entry.get("task_id")
    if task_id is not None:
        task_kwargs["task_id"] = _parse_uuid(task_id)
    return task_kwargs


def _parse_uuid(value: Any) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise TaskImportError("Task IDs must be valid UUID strings.") from exc


class ImportStrategy(Protocol):
    """Strategy for merging imported tasks with existing ones."""

    name: str

    def apply(self, existing: Sequence[Task], imported: Sequence[Task]) -> list[Task]:
        """Return the merged task list."""
        ...


class AppendImportStrategy:
    name = "append"

    def apply(self, existing: Sequence[Task], imported: Sequence[Task]) -> list[Task]:
        return list(existing) + list(imported)


class ReplaceImportStrategy:
    name = "replace"

    def apply(self, existing: Sequence[Task], imported: Sequence[Task]) -> list[Task]:
        return list(imported)


class MergeByIdImportStrategy:
    """
    Merge tasks by UUID, replacing matching root-level tasks and appending new ones.
    """

    name = "merge"

    def apply(self, existing: Sequence[Task], imported: Sequence[Task]) -> list[Task]:
        merged = list(existing)
        index_by_id = {task.task_id: idx for idx, task in enumerate(merged)}
        for incoming in imported:
            position = index_by_id.get(incoming.task_id)
            if position is not None:
                merged[position] = incoming
            else:
                index_by_id[incoming.task_id] = len(merged)
                merged.append(incoming)
        return merged


DEFAULT_IMPORT_STRATEGIES: dict[str, ImportStrategy] = {
    strategy.name: strategy
    for strategy in (
        AppendImportStrategy(),
        ReplaceImportStrategy(),
        MergeByIdImportStrategy(),
    )
}


def get_import_strategy(name: str) -> ImportStrategy:
    try:
        return DEFAULT_IMPORT_STRATEGIES[name.lower()]
    except KeyError as exc:
        raise TaskImportError(f"Unknown import strategy '{name}'.") from exc
