from __future__ import annotations

from typing import Iterable
from uuid import UUID

from tasky_models import Task

from .hooks import HookBusPort, NullHookBus
from .importers import ImportStrategy
from .repositories import TaskRepository
from .tasks import TaskFactory, TaskTreeBuilder, TaskUseCases


class TaskService:
    """High-level façade over task use-case functions."""

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

    def _use_cases(self) -> TaskUseCases:
        return TaskUseCases(
            repository=self._repository,
            task_factory=self._task_factory,
            tree_builder=self._tree_builder,
            hook_bus=self._hook_bus,
        )

    def list(self) -> list[Task]:
        return self._use_cases().list()

    def create(
        self,
        name: str,
        details: str,
        *,
        parent_id: str | None = None,
    ) -> Task:
        return self._use_cases().create(name=name, details=details, parent_id=parent_id)

    def remove(self, task_id: str) -> Task:
        return self._use_cases().remove(task_id)

    def replace(self, tasks: Iterable[Task]) -> None:
        self._use_cases().replace(tasks)

    def import_tasks(
        self,
        imported: Iterable[Task],
        strategy: ImportStrategy,
    ) -> list[Task]:
        return self._use_cases().import_tasks(imported, strategy)

    def export(self) -> list[Task]:
        return self._use_cases().export()

    def complete(self, task_id: str | UUID) -> Task:
        return self._use_cases().complete(task_id)

    def reopen(self, task_id: str | UUID) -> Task:
        return self._use_cases().reopen(task_id)

    def update(
        self,
        task_id: str | UUID,
        *,
        name: str | None = None,
        details: str | None = None,
    ) -> Task:
        return self._use_cases().update(task_id, name=name, details=details)
