from __future__ import annotations

from uuid import UUID
from typing import Any, Callable

import pytest

from tasky_core import (
    HookBusPort,
    HookEvent,
    TaskPostAddPayload,
    TaskPostCompletePayload,
    TaskPostImportPayload,
    TaskPostRemovePayload,
    TaskPostUpdatePayload,
    TaskPreAddPayload,
    TaskPreCompletePayload,
    TaskPreImportPayload,
    TaskPreRemovePayload,
    TaskPreUpdatePayload,
    get_import_strategy,
)
from tasky_core.tasks import TaskNotFoundError, TaskUseCases, TaskValidationError
from tasky_storage import JsonDocumentStore, JsonTaskRepository
from tasky_models import Task


def _use_cases(tmp_path, hook_bus: HookBusPort | None = None):
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)
    return TaskUseCases(repository=repo, hook_bus=hook_bus), repo


def test_create_task_rejects_blank_name(tmp_path) -> None:
    use_cases, _ = _use_cases(tmp_path)
    with pytest.raises(TaskValidationError):
        use_cases.create(name=" ", details="desc")


def test_create_subtask_appends_to_parent(tmp_path) -> None:
    use_cases, repo = _use_cases(tmp_path)
    parent = use_cases.create(name="Parent", details="Top")

    subtask = use_cases.create(
        name="Child",
        details="Nested",
        parent_id=str(parent.task_id),
    )

    stored_parent = repo.list_tasks()[0]
    assert stored_parent.subtasks[0].task_id == subtask.task_id


def test_create_subtask_raises_when_parent_missing(tmp_path) -> None:
    use_cases, _ = _use_cases(tmp_path)
    use_cases.create(name="Parent", details="Top")

    with pytest.raises(TaskNotFoundError):
        use_cases.create(
            name="Child",
            details="Nested",
            parent_id=str(UUID(int=1)),
        )


def test_remove_subtask(tmp_path) -> None:
    use_cases, repo = _use_cases(tmp_path)
    parent = use_cases.create(name="Parent", details="Top")
    child = use_cases.create(
        name="Child",
        details="Nested",
        parent_id=str(parent.task_id),
    )
    before = repo.list_tasks()[0].updated_at

    removed = use_cases.remove(child.task_id)

    stored_parent = repo.list_tasks()[0]
    assert removed.task_id == child.task_id
    assert stored_parent.subtasks == []
    assert stored_parent.updated_at >= before


def test_remove_missing_task_raises(tmp_path) -> None:
    use_cases, _ = _use_cases(tmp_path)
    with pytest.raises(TaskNotFoundError):
        use_cases.remove(UUID(int=1))


def test_create_task_normalizes_inputs(tmp_path) -> None:
    use_cases, repo = _use_cases(tmp_path)

    created = use_cases.create(name="  Foo   Bar  ", details="  Trim  ")

    stored = repo.list_tasks()[0]
    assert created.name == "Foo Bar"
    assert created.details == "Trim"
    assert stored.name == "Foo Bar"
    assert stored.details == "Trim"


def test_create_task_uses_hook_bus_for_mutation(tmp_path) -> None:
    bus = RecordingHookBus()

    def mutate(payload: TaskPreAddPayload) -> TaskPreAddPayload:
        return TaskPreAddPayload(
            name="Hooked Name",
            details="Hooked Details",
            parent_id=payload.parent_id,
        )

    bus.set_mutation(HookEvent.TASK_PRE_ADD, mutate)
    use_cases, repo = _use_cases(tmp_path, hook_bus=bus)

    created = use_cases.create(name="Original", details="Desc")

    assert created.name == "Hooked Name"
    assert repo.list_tasks()[0].name == "Hooked Name"
    emitted = bus.last_emit(HookEvent.TASK_POST_ADD)
    assert isinstance(emitted, TaskPostAddPayload)
    assert emitted.task["name"] == "Hooked Name"


def test_remove_task_emits_hooks(tmp_path) -> None:
    bus = RecordingHookBus()
    use_cases, repo = _use_cases(tmp_path, hook_bus=bus)
    task = use_cases.create(name="Remove-me", details="bye")

    def mutate(payload: TaskPreRemovePayload) -> TaskPreRemovePayload:
        assert payload.task_id
        return TaskPreRemovePayload(task_id=str(task.task_id))

    bus.set_mutation(HookEvent.TASK_PRE_REMOVE, mutate)

    removed = use_cases.remove("ignored")

    assert removed.task_id == task.task_id
    emitted = bus.last_emit(HookEvent.TASK_POST_REMOVE)
    assert isinstance(emitted, TaskPostRemovePayload)
    assert emitted.task["task_id"] == str(task.task_id)


def test_import_tasks_respects_hook_mutations(tmp_path) -> None:
    bus = RecordingHookBus()
    use_cases, repo = _use_cases(tmp_path, hook_bus=bus)
    repo.upsert_task(Task.create(name="Existing", details="persisted"))

    def mutate(payload: TaskPreImportPayload) -> TaskPreImportPayload:
        injected = Task.create(name="Hooked", details="External")
        return TaskPreImportPayload(
            strategy="replace",
            tasks=[injected.model_dump(mode="json")],
        )

    bus.set_mutation(HookEvent.TASK_PRE_IMPORT, mutate)

    result = use_cases.import_tasks(
        [Task.create(name="Ignored", details="Ignored")],
        strategy=get_import_strategy("append"),
    )

    assert len(result) == 1
    assert result[0].name == "Hooked"
    emitted = bus.last_emit(HookEvent.TASK_POST_IMPORT)
    assert isinstance(emitted, TaskPostImportPayload)
    assert emitted.strategy == "replace"
    assert emitted.imported == 1


def test_complete_task_marks_completed_and_emits_hooks(tmp_path) -> None:
    bus = RecordingHookBus()
    use_cases, repo = _use_cases(tmp_path, hook_bus=bus)
    created = use_cases.create(name="Complete me", details="pending")

    def mutate(payload: TaskPreCompletePayload) -> TaskPreCompletePayload:
        return TaskPreCompletePayload(task_id=str(created.task_id))

    bus.set_mutation(HookEvent.TASK_PRE_COMPLETE, mutate)

    updated = use_cases.complete("ignored")

    stored = repo.list_tasks()[0]
    assert updated.completed
    assert stored.completed
    emitted = bus.last_emit(HookEvent.TASK_POST_COMPLETE)
    assert isinstance(emitted, TaskPostCompletePayload)
    assert emitted.task["completed"] is True


def test_reopen_task_marks_incomplete(tmp_path) -> None:
    use_cases, repo = _use_cases(tmp_path)
    task = use_cases.create(name="Done", details="done")
    use_cases.complete(task.task_id)

    reopened = use_cases.reopen(task.task_id)

    stored = repo.list_tasks()[0]
    assert reopened.completed is False
    assert stored.completed is False


def test_update_task_requires_changes(tmp_path) -> None:
    use_cases, _ = _use_cases(tmp_path)
    task = use_cases.create(name="Name", details="Details")
    with pytest.raises(TaskValidationError):
        use_cases.update(task.task_id)


def test_update_task_applies_changes_with_hooks(tmp_path) -> None:
    bus = RecordingHookBus()
    use_cases, repo = _use_cases(tmp_path, hook_bus=bus)
    task = use_cases.create(name="Original", details="Before")

    def mutate(payload: TaskPreUpdatePayload) -> TaskPreUpdatePayload:
        assert payload.name == "New Name"
        return TaskPreUpdatePayload(
            task_id=payload.task_id,
            name="Hooked Name",
            details=payload.details,
        )

    bus.set_mutation(HookEvent.TASK_PRE_UPDATE, mutate)

    updated = use_cases.update(task.task_id, name="New Name")

    stored = repo.list_tasks()[0]
    assert updated.name == "Hooked Name"
    assert stored.name == "Hooked Name"
    emitted = bus.last_emit(HookEvent.TASK_POST_UPDATE)
    assert isinstance(emitted, TaskPostUpdatePayload)
    assert emitted.task["name"] == "Hooked Name"


def test_export_returns_current_tasks(tmp_path) -> None:
    use_cases, _ = _use_cases(tmp_path)
    use_cases.create(name="One", details="Details")

    exported = use_cases.export()

    assert len(exported) == 1
    assert exported[0].name == "One"


class RecordingHookBus(HookBusPort):
    def __init__(self) -> None:
        self._mutations: dict[HookEvent, Callable[[Any], Any]] = {}
        self.events: list[tuple[str, HookEvent, Any]] = []

    def set_mutation(self, event: HookEvent, handler: Callable[[Any], Any]) -> None:
        self._mutations[event] = handler

    def last_emit(self, event: HookEvent) -> Any | None:
        for phase, recorded_event, payload in reversed(self.events):
            if phase == "emit" and recorded_event == event:
                return payload
        return None

    def is_enabled(self) -> bool:
        return True

    def mutate(self, event: HookEvent, payload):
        handler = self._mutations.get(event)
        self.events.append(("mutate", event, payload))
        if handler is None:
            return payload
        return handler(payload)

    def emit(self, event: HookEvent, payload=None) -> None:
        self.events.append(("emit", event, payload))
