from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from tasky_core.repositories import TaskRepositoryError
from tasky_models import Task
from tasky_storage import JsonDocumentStore, JsonTaskRepository, SQLiteTaskRepository


def make_task(name: str, details: str, task_id: UUID | None = None) -> Task:
    data = {"name": name, "details": details}
    if task_id is not None:
        data["task_id"] = task_id
    return Task(**data)


def test_list_tasks_returns_empty_when_store_empty(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)

    assert repo.list_tasks() == []


def test_upsert_task_persists_new_task(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)
    task = make_task("Write docs", "Document storage adapter")

    repo.upsert_task(task)

    stored = repo.list_tasks()
    assert len(stored) == 1
    assert stored[0].name == "Write docs"


def test_upsert_task_replaces_existing_entry(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)
    task_id = uuid4()
    task = make_task("Write docs", "Document storage adapter", task_id=task_id)
    repo.upsert_task(task)

    updated = task.model_copy(update={"completed": True})
    repo.upsert_task(updated)

    stored = repo.list_tasks()
    assert stored[0].completed is True


def test_delete_task_removes_existing_entry(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)
    task = make_task("Write docs", "Document storage adapter")
    repo.upsert_task(task)

    repo.delete_task(task.task_id)

    assert repo.list_tasks() == []


def test_delete_task_raises_when_missing(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)

    with pytest.raises(TaskRepositoryError):
        repo.delete_task("non-existent")


def test_replace_tasks_overwrites_existing_document(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    repo = JsonTaskRepository(store)
    repo.upsert_task(make_task("Write docs", "Initial"))

    new_tasks = [
        make_task("Review", "Second"),
        make_task("Ship", "Third"),
    ]
    repo.replace_tasks(new_tasks)

    stored = repo.list_tasks()
    assert {task.name for task in stored} == {"Review", "Ship"}


def test_invalid_payload_raises_error(tmp_path) -> None:
    store = JsonDocumentStore(tmp_path / "tasks.json")
    store.save({"tasks": ["not-a-dict"]})
    repo = JsonTaskRepository(store)

    with pytest.raises(TaskRepositoryError):
        repo.list_tasks()


def test_sqlite_repository_persists_and_retrieves_tree(tmp_path) -> None:
    database = tmp_path / "tasks.sqlite"
    repo = SQLiteTaskRepository(database)
    parent = make_task("Parent", "root")
    child = make_task("Child", "leaf")
    parent.add_subtask(child)

    repo.upsert_task(parent)

    stored = repo.list_tasks()
    assert len(stored) == 1
    assert stored[0].subtasks[0].name == "Child"


def test_sqlite_repository_replace_tasks(tmp_path) -> None:
    database = tmp_path / "tasks.sqlite"
    repo = SQLiteTaskRepository(database)
    repo.upsert_task(make_task("Old", "task"))

    repo.replace_tasks(
        [
            make_task("New A", "first"),
            make_task("New B", "second"),
        ]
    )

    names = [task.name for task in repo.list_tasks()]
    assert names == ["New A", "New B"]


def test_sqlite_repository_delete_missing_raises(tmp_path) -> None:
    repo = SQLiteTaskRepository(tmp_path / "tasks.sqlite")

    with pytest.raises(TaskRepositoryError):
        repo.delete_task(uuid4())
