from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from tasky_core.task_tree import TaskTree
from tasky_core.tasks import TaskUseCases
from tasky_core.importers import AppendImportStrategy
from tasky_models import Task


class FakeRepository:
    def __init__(self, tasks: list[Task] | None = None) -> None:
        self._tasks = list(tasks or [])

    def list_tasks(self) -> list[Task]:
        return list(self._tasks)

    def get_task(self, task_id: str | UUID) -> Task:
        for task in self._tasks:
            if str(task.task_id) == str(task_id):
                return task
        raise LookupError(task_id)

    def upsert_task(self, task: Task) -> Task:
        for index, existing in enumerate(self._tasks):
            if existing.task_id == task.task_id:
                self._tasks[index] = task
                break
        else:
            self._tasks.append(task)
        return task

    def delete_task(self, task_id: str | UUID) -> None:
        before = len(self._tasks)
        self._tasks = [task for task in self._tasks if str(task.task_id) != str(task_id)]
        if len(self._tasks) == before:
            raise LookupError(task_id)

    def replace_tasks(self, tasks: list[Task]) -> None:
        self._tasks = list(tasks)


class RecordingFactory:
    def __init__(self, committed: Task | None = None) -> None:
        self.called_with: tuple[str, str] | None = None
        self.result = committed or Task(name="stub", details="stub")

    def build(self, name: str, details: str) -> Task:
        self.called_with = (name, details)
        return self.result


class RecordingTreeBuilder:
    def __init__(self) -> None:
        self.calls = 0

    def build(self, tasks: list[Task]) -> TaskTree:
        self.calls += 1
        return TaskTree(tasks)


def test_task_usecases_create_uses_custom_factory() -> None:
    repo = FakeRepository()
    produced = Task(name="Provided", details="Through factory")
    factory = RecordingFactory(committed=produced)
    use_cases = TaskUseCases(repository=repo, task_factory=factory)

    created = use_cases.create(name="Provided", details="Through factory")

    assert factory.called_with == ("Provided", "Through factory")
    assert created is produced
    assert repo.list_tasks()[0] is produced


def test_task_usecases_remove_uses_tree_builder_for_nested_tasks() -> None:
    child = Task(name="Child", details="nested")
    parent = Task(name="Parent", details="root", subtasks=[child])
    repo = FakeRepository(tasks=[parent])
    builder = RecordingTreeBuilder()
    use_cases = TaskUseCases(repository=repo, tree_builder=builder)

    removed = use_cases.remove(child.task_id)

    assert removed.task_id == child.task_id
    assert builder.calls == 1
    assert len(repo.list_tasks()[0].subtasks) == 0


def test_task_usecases_list_sorts_by_created_timestamp() -> None:
    now = datetime.now(timezone.utc)
    earlier = Task(name="Old", details="task", created_at=now)
    later = Task(name="New", details="task", created_at=now + timedelta(seconds=1))
    repo = FakeRepository(tasks=[later, earlier])
    use_cases = TaskUseCases(repository=repo)

    tasks = use_cases.list()

    assert [task.name for task in tasks] == ["Old", "New"]


def test_task_usecases_import_tasks_applies_strategy() -> None:
    repo = FakeRepository()
    strategy = AppendImportStrategy()
    use_cases = TaskUseCases(repository=repo)
    incoming = [Task(name="New", details="task")]

    merged = use_cases.import_tasks(incoming, strategy)

    assert merged[0].name == "New"
    assert len(repo.list_tasks()) == 1
