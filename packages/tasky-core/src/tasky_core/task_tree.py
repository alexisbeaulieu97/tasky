from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Tuple
from uuid import UUID

from tasky_models import Task


@dataclass(frozen=True)
class TaskLocation:
    task: Task | None
    parent: Task | None


class TaskTree:
    """Utility for navigating and mutating task aggregates."""

    def __init__(self, tasks: Iterable[Task]) -> None:
        self._tasks: list[Task] = list(tasks)

    def roots(self) -> list[Task]:
        """Return a shallow copy of the root task list."""
        return list(self._tasks)

    def find(self, task_id: UUID) -> Task | None:
        location = self.find_with_parent(task_id)
        return location.task

    def find_with_parent(self, task_id: UUID) -> TaskLocation:
        return TaskLocation(*_find_with_parent(self._tasks, task_id))

    def add_subtask(self, parent_id: UUID, subtask: Task) -> bool:
        parent = self.find(parent_id)
        if parent is None:
            return False
        parent.add_subtask(subtask)
        return True

    def remove_subtask(self, task_id: UUID) -> Task | None:
        target, parent = _find_with_parent(self._tasks, task_id)
        if target is None or parent is None:
            return None
        if not parent.remove_subtask(task_id):
            return None
        return target


@dataclass(frozen=True)
class FlattenedTask:
    task: Task
    depth: int
    is_last: bool
    lineage: Tuple[bool, ...]


def flatten_tasks(tasks: Iterable[Task]) -> Iterator[FlattenedTask]:
    """
    Yield tasks depth-first alongside lineage metadata.
    """
    yield from _flatten(list(tasks), lineage=())


def count_tasks(tasks: Iterable[Task]) -> tuple[int, int]:
    """
    Return (remaining, total) counts for the provided task tree.
    """
    remaining = 0
    total = 0
    for task in tasks:
        total += 1
        if not task.completed:
            remaining += 1
        child_remaining, child_total = count_tasks(task.subtasks)
        remaining += child_remaining
        total += child_total
    return remaining, total


def _find_with_parent(
    tasks: list[Task],
    target: UUID,
    parent: Task | None = None,
) -> tuple[Optional[Task], Optional[Task]]:
    for task in tasks:
        if task.task_id == target:
            return task, parent
        located, located_parent = _find_with_parent(task.subtasks, target, task)
        if located is not None:
            return located, located_parent
    return None, None


def _flatten(tasks: list[Task], lineage: Tuple[bool, ...]) -> Iterator[FlattenedTask]:
    depth = len(lineage)
    count = len(tasks)
    for index, task in enumerate(tasks):
        is_last = index == count - 1
        yield FlattenedTask(
            task=task,
            depth=depth,
            is_last=is_last,
            lineage=lineage,
        )
        if task.subtasks:
            yield from _flatten(list(task.subtasks), lineage=lineage + (is_last,))
