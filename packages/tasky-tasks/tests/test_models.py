"""Tests for TaskModel timestamp behavior."""

from __future__ import annotations

from datetime import UTC
from time import sleep

from tasky_tasks.models import TaskModel


def test_task_creation_sets_utc_timestamps() -> None:
    """Verify TaskModel assigns UTC-aware timestamps on creation."""
    task = TaskModel(name="Sample Task", details="Details")

    assert task.created_at.tzinfo == UTC
    assert task.updated_at.tzinfo == UTC


def test_created_and_updated_start_equal() -> None:
    """Verify created_at and updated_at start with the same value."""
    task = TaskModel(name="Sample Task", details="Details")

    assert task.created_at == task.updated_at


def test_mark_updated_changes_timestamp() -> None:
    """Verify mark_updated refreshes the updated_at timestamp."""
    task = TaskModel(name="Sample Task", details="Details")
    original_updated_at = task.updated_at

    sleep(0.01)
    task.mark_updated()

    assert task.updated_at > original_updated_at
    assert task.updated_at.tzinfo == UTC


def test_mark_updated_preserves_created_at() -> None:
    """Verify mark_updated keeps created_at unchanged."""
    task = TaskModel(name="Sample Task", details="Details")
    created_at = task.created_at

    sleep(0.01)
    task.mark_updated()

    assert task.created_at == created_at


def test_timestamps_serializable() -> None:
    """Verify TaskModel serializes and deserializes timestamps correctly."""
    task = TaskModel(name="Sample Task", details="Details")

    json_payload = task.model_dump_json()
    restored = TaskModel.model_validate_json(json_payload)

    assert restored.created_at == task.created_at
    assert restored.updated_at == task.updated_at
    assert restored.created_at.tzinfo == UTC
    assert restored.updated_at.tzinfo == UTC
