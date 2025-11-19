"""Tests for event models."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from tasky_hooks.events import (
    TaskCreatedEvent,
    TaskSnapshot,
    TaskUpdatedEvent,
)


def test_task_snapshot_creation() -> None:
    """Test creating a task snapshot."""
    snapshot = TaskSnapshot(
        task_id=uuid4(),
        name="Test Task",
        details="Details",
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert snapshot.name == "Test Task"
    assert snapshot.status == "pending"


def test_event_immutability() -> None:
    """Test that events are immutable."""
    task_id = uuid4()
    event = TaskCreatedEvent(
        task_id=task_id,
        task_snapshot=TaskSnapshot(
            task_id=task_id,
            name="Test",
            details="Details",
            status="pending",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        project_root="/tmp",  # noqa: S108
    )

    with pytest.raises(ValidationError):
        event.project_root = "/other"  # type: ignore[misc]


def test_event_serialization() -> None:
    """Test event serialization to JSON."""
    task_id = uuid4()
    timestamp = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)

    event = TaskCreatedEvent(
        task_id=task_id,
        timestamp=timestamp,
        task_snapshot=TaskSnapshot(
            task_id=task_id,
            name="Test",
            details="Details",
            status="pending",
            created_at=timestamp,
            updated_at=timestamp,
        ),
        project_root="/tmp",  # noqa: S108
    )

    json_str = event.model_dump_json()
    assert str(task_id) in json_str
    assert "2025-01-01T12:00:00Z" in json_str
    assert "task_created" in json_str


def test_task_updated_event() -> None:
    """Test TaskUpdatedEvent structure."""
    task_id = uuid4()
    old_snapshot = TaskSnapshot(
        task_id=task_id,
        name="Old",
        details="Details",
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    new_snapshot = TaskSnapshot(
        task_id=task_id,
        name="New",
        details="Details",
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    event = TaskUpdatedEvent(
        task_id=task_id,
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        updated_fields=["name"],
    )

    assert event.updated_fields == ["name"]
    assert event.old_snapshot.name == "Old"
    assert event.new_snapshot.name == "New"
