from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import UUID

from pydantic import ValidationError

from tasky_models import Task

from .hooks import (
    HookBusPort,
    HookEvent,
    NullHookBus,
    TaskPostAddPayload,
    TaskPostCompletePayload,
    TaskPostImportPayload,
    TaskPostRemovePayload,
    TaskPostReopenPayload,
    TaskPostUpdatePayload,
    TaskPreAddPayload,
    TaskPreCompletePayload,
    TaskPreImportPayload,
    TaskPreRemovePayload,
    TaskPreReopenPayload,
    TaskPreUpdatePayload,
)
from .importers import ImportStrategy, TaskImportError, get_import_strategy
from .repositories import TaskRepository, TaskRepositoryError
from .task_tree import TaskTree


class TaskUseCaseError(Exception):
    """Base exception raised by task use-case orchestration."""


class TaskValidationError(TaskUseCaseError):
    """Raised when user input fails validation."""


class TaskNotFoundError(TaskUseCaseError):
    """Raised when the requested task cannot be located."""


def _parse_task_id(task_id: str | UUID) -> UUID:
    if isinstance(task_id, UUID):
        return task_id
    try:
        return UUID(str(task_id))
    except (TypeError, ValueError) as exc:
        raise TaskValidationError("Task ID must be a valid UUID.") from exc


@dataclass(frozen=True)
class TaskFactory:
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)

    def build(self, name: str, details: str) -> Task:
        try:
            return Task.create(name=name, details=details, clock=self.clock)
        except (ValueError, ValidationError) as exc:
            raise TaskValidationError(str(exc)) from exc


class TaskTreeBuilder:
    def build(self, tasks: Iterable[Task]) -> TaskTree:
        return TaskTree(tasks)


class TaskUseCases:
    def __init__(
        self,
        repository: TaskRepository,
        *,
        task_factory: TaskFactory | None = None,
        tree_builder: TaskTreeBuilder | None = None,
        hook_bus: HookBusPort | None = None,
    ) -> None:
        self._repository = repository
        self._task_factory = task_factory or TaskFactory()
        self._tree_builder = tree_builder or TaskTreeBuilder()
        self._hook_bus = hook_bus or NullHookBus()

    def list(self) -> list[Task]:
        try:
            tasks = self._repository.list_tasks()
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Unable to retrieve tasks from storage.") from exc
        return sorted(tasks, key=lambda task: task.created_at)

    def create(
        self,
        name: str,
        details: str,
        *,
        parent_id: str | UUID | None = None,
    ) -> Task:
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_ADD,
            TaskPreAddPayload(
                name=name,
                details=details,
                parent_id=_string_or_none(parent_id),
            ),
        )
        task = self._task_factory.build(payload.name, payload.details)
        persisted = (
            self._persist_root(task)
            if payload.parent_id is None
            else self._persist_subtask(task, payload.parent_id)
        )
        self._hook_bus.emit(
            HookEvent.TASK_POST_ADD,
            TaskPostAddPayload(task=_task_payload(persisted)),
        )
        return persisted

    def remove(self, task_id: str | UUID) -> Task:
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_REMOVE,
            TaskPreRemovePayload(task_id=str(task_id)),
        )
        identifier = _parse_task_id(payload.task_id)
        tree = self._load_tree()
        location = tree.find_with_parent(identifier)
        located = location.task
        if located is None:
            raise TaskNotFoundError(f"Task '{identifier}' not found.")

        removed = (
            self._remove_root(identifier, located)
            if location.parent is None
            else self._remove_nested(tree, identifier, located)
        )
        self._hook_bus.emit(
            HookEvent.TASK_POST_REMOVE,
            TaskPostRemovePayload(task=_task_payload(removed)),
        )
        return removed

    def replace(self, tasks: Iterable[Task]) -> None:
        try:
            self._repository.replace_tasks(tasks)
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to replace the task collection.") from exc

    def import_tasks(
        self,
        imported: Iterable[Task],
        strategy: ImportStrategy,
    ) -> list[Task]:
        incoming = list(imported)
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_IMPORT,
            TaskPreImportPayload(
                strategy=strategy.name,
                tasks=[_task_payload(task) for task in incoming],
            ),
        )
        strategy = _resolve_import_strategy(strategy, payload.strategy)
        try:
            tasks_to_add = _tasks_from_payload(payload.tasks)
        except ValidationError as exc:
            raise TaskUseCaseError("Hook payload produced invalid tasks.") from exc
        existing = self._load_all()
        merged = strategy.apply(existing, tasks_to_add)
        self.replace(merged)
        self._hook_bus.emit(
            HookEvent.TASK_POST_IMPORT,
            TaskPostImportPayload(strategy=strategy.name, imported=len(tasks_to_add)),
        )
        return merged

    def export(self) -> list[Task]:
        return self._load_all()

    def complete(self, task_id: str | UUID) -> Task:
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_COMPLETE,
            TaskPreCompletePayload(task_id=str(task_id)),
        )
        identifier = _parse_task_id(payload.task_id)
        target, tree = self._locate_task(identifier)
        target.mark_complete()
        self._persist_tree(tree)
        self._hook_bus.emit(
            HookEvent.TASK_POST_COMPLETE,
            TaskPostCompletePayload(task=_task_payload(target)),
        )
        return target

    def reopen(self, task_id: str | UUID) -> Task:
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_REOPEN,
            TaskPreReopenPayload(task_id=str(task_id)),
        )
        identifier = _parse_task_id(payload.task_id)
        target, tree = self._locate_task(identifier)
        target.mark_incomplete()
        self._persist_tree(tree)
        self._hook_bus.emit(
            HookEvent.TASK_POST_REOPEN,
            TaskPostReopenPayload(task=_task_payload(target)),
        )
        return target

    def update(
        self,
        task_id: str | UUID,
        *,
        name: str | None = None,
        details: str | None = None,
    ) -> Task:
        payload = self._hook_bus.mutate(
            HookEvent.TASK_PRE_UPDATE,
            TaskPreUpdatePayload(task_id=str(task_id), name=name, details=details),
        )
        identifier = _parse_task_id(payload.task_id)
        if payload.name is None and payload.details is None:
            raise TaskValidationError("Provide a new name or details to update the task.")
        target, tree = self._locate_task(identifier)
        before = (target.name, target.details)
        target.update_content(name=payload.name, details=payload.details)
        if before == (target.name, target.details):
            raise TaskValidationError("Task update produced no changes.")
        self._persist_tree(tree)
        self._hook_bus.emit(
            HookEvent.TASK_POST_UPDATE,
            TaskPostUpdatePayload(task=_task_payload(target)),
        )
        return target

    def _persist_root(self, task: Task) -> Task:
        try:
            return self._repository.upsert_task(task)
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to persist the new task.") from exc

    def _persist_subtask(self, task: Task, parent_id: str | UUID) -> Task:
        parent_uuid = _parse_task_id(parent_id)
        tree = self._load_tree()
        if not tree.add_subtask(parent_uuid, task):
            raise TaskNotFoundError(f"Parent task '{parent_uuid}' not found.")
        try:
            self._repository.replace_tasks(tree.roots())
            return task
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to persist the new subtask.") from exc

    def _remove_root(self, identifier: UUID, task: Task) -> Task:
        try:
            self._repository.delete_task(identifier)
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to remove the requested task.") from exc
        return task

    def _remove_nested(self, tree: TaskTree, identifier: UUID, task: Task) -> Task:
        removed = tree.remove_subtask(identifier)
        if removed is None:
            raise TaskUseCaseError("Failed to remove the requested subtask.")
        try:
            self._repository.replace_tasks(tree.roots())
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to remove the requested subtask.") from exc
        return task

    def _load_tree(self) -> TaskTree:
        try:
            tasks = self._repository.list_tasks()
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Unable to retrieve tasks from storage.") from exc
        return self._tree_builder.build(tasks)

    def _load_all(self) -> list[Task]:
        try:
            return self._repository.list_tasks()
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Unable to retrieve tasks from storage.") from exc

    def _locate_task(self, identifier: UUID) -> tuple[Task, TaskTree]:
        tree = self._load_tree()
        location = tree.find_with_parent(identifier)
        task = location.task
        if task is None:
            raise TaskNotFoundError(f"Task '{identifier}' not found.")
        return task, tree

    def _persist_tree(self, tree: TaskTree) -> None:
        try:
            self._repository.replace_tasks(tree.roots())
        except TaskRepositoryError as exc:
            raise TaskUseCaseError("Failed to persist task changes.") from exc


def _task_payload(task: Task) -> dict[str, Any]:
    return task.model_dump(mode="json")


def _tasks_from_payload(raw_tasks: Sequence[Mapping[str, Any]]) -> list[Task]:
    converted: list[Task] = []
    for item in raw_tasks:
        converted.append(Task.model_validate(dict(item)))
    return converted


def _string_or_none(value: str | UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _resolve_import_strategy(
    current: ImportStrategy,
    requested_name: str | None,
) -> ImportStrategy:
    if requested_name is None:
        return current
    if requested_name.lower() == current.name.lower():
        return current
    try:
        return get_import_strategy(requested_name)
    except TaskImportError as exc:
        raise TaskUseCaseError(str(exc)) from exc
