from __future__ import annotations


from datetime import datetime, timezone

import pytest

from tasky_models import Task


def test_add_subtask_updates_timestamp(monkeypatch) -> None:
    parent = Task(name="Parent", details="root")
    child = Task(name="Child", details="leaf")

    before = parent.updated_at
    parent.add_subtask(child)

    assert parent.subtasks[-1] is child
    assert parent.updated_at >= before


def test_remove_subtask_returns_flag_and_updates_timestamp() -> None:
    child = Task(name="Child", details="leaf")
    parent = Task(name="Parent", details="root", subtasks=[child])

    before = parent.updated_at
    removed = parent.remove_subtask(child.task_id)

    assert removed is True
    assert parent.subtasks == []
    assert parent.updated_at >= before

    after = parent.updated_at
    removed_again = parent.remove_subtask(child.task_id)
    assert removed_again is False
    assert parent.updated_at == after


def test_mark_complete_and_incomplete_toggle() -> None:
    task = Task(name="Demo", details="toggle")

    before = task.updated_at
    task.mark_complete()
    assert task.completed is True
    assert task.updated_at >= before

    after = task.updated_at
    task.mark_incomplete()
    assert task.completed is False
    assert task.updated_at >= after


def test_task_create_sanitizes_inputs() -> None:
    task = Task.create(name="  Foo   Bar  ", details="\n\n summary \n ")

    assert task.name == "Foo Bar"
    assert task.details == "summary"
    assert task.created_at == task.updated_at


def test_task_create_uses_provided_clock() -> None:
    moment = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    task = Task.create(name="Clocked", details="Task", clock=lambda: moment)

    assert task.created_at == moment
    assert task.updated_at == moment


def test_task_create_rejects_blank_fields() -> None:
    with pytest.raises(ValueError):
        Task.create(name=" ", details="Valid")

    with pytest.raises(ValueError):
        Task.create(name="Valid", details=" ")


def test_update_content_normalizes_and_refreshes_timestamp() -> None:
    task = Task(name="Original", details="Detail")
    before = task.updated_at

    task.update_content(name="  Renamed  ", details="  Trimmed  ")

    assert task.name == "Renamed"
    assert task.details == "Trimmed"
    assert task.updated_at >= before
