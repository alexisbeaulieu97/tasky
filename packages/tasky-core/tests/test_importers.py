import json

import pytest

from uuid import uuid4

from tasky_core.importers import (
    AppendImportStrategy,
    MergeByIdImportStrategy,
    ReplaceImportStrategy,
    TaskImportError,
    load_tasks_from_json,
)


def test_load_tasks_from_json_parses_nested_structure() -> None:
    payload = json.dumps(
        [
            {
                "name": "Parent",
                "details": "root",
                "subtasks": [
                    {"name": "Child", "details": "nested", "completed": True}
                ],
            }
        ]
    )

    tasks = load_tasks_from_json(payload)

    assert len(tasks) == 1
    parent = tasks[0]
    assert parent.name == "Parent"
    assert parent.subtasks[0].name == "Child"
    assert parent.subtasks[0].completed is True


def test_load_tasks_from_json_rejects_invalid_payload() -> None:
    with pytest.raises(TaskImportError):
        load_tasks_from_json("{}")


def test_load_tasks_from_json_accepts_explicit_task_ids() -> None:
    identifier = str(uuid4())
    payload = json.dumps([{"task_id": identifier, "name": "Task", "details": "desc"}])

    tasks = load_tasks_from_json(payload)

    assert str(tasks[0].task_id) == identifier


def test_append_strategy_concatenates_tasks(sample_tasks) -> None:
    strategy = AppendImportStrategy()

    result = strategy.apply(sample_tasks[:1], sample_tasks[1:])

    assert [task.name for task in result] == ["A", "B"]


def test_replace_strategy_overwrites_existing(sample_tasks) -> None:
    strategy = ReplaceImportStrategy()

    result = strategy.apply(sample_tasks[:1], sample_tasks[1:])

    assert [task.name for task in result] == ["B"]


def test_merge_strategy_replaces_matching_ids(sample_tasks) -> None:
    existing_task = sample_tasks[0]
    replacement_task = existing_task.model_copy(deep=True)
    replacement_task.details = "updated"
    strategy = MergeByIdImportStrategy()

    result = strategy.apply([existing_task], [replacement_task])

    assert len(result) == 1
    assert result[0].details == "updated"


@pytest.fixture()
def sample_tasks():
    return [
        load_tasks_from_json(json.dumps([{"name": "A", "details": "one"}]))[0],
        load_tasks_from_json(json.dumps([{"name": "B", "details": "two"}]))[0],
    ]
