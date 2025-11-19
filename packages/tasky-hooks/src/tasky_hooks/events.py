"""Event definitions for task lifecycle hooks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskSnapshot(BaseModel):
    """A snapshot of a task's state at a specific point in time.

    This model mirrors the structure of TaskModel but is decoupled from the
    tasky-tasks package to avoid circular dependencies.
    """

    model_config = ConfigDict(frozen=True)

    task_id: UUID
    name: str
    details: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Future extensibility for tags, subtasks, etc.
    tags: list[str] = Field(default_factory=list)
    subtasks: list[Any] = Field(default_factory=list)
    blocked_by: list[Any] = Field(default_factory=list)


class BaseEvent(BaseModel):
    """Base class for all task lifecycle events."""

    model_config = ConfigDict(frozen=True)

    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1.0"


class TaskCreatedEvent(BaseEvent):
    """Event emitted when a task is created."""

    event_type: str = "task_created"
    task_id: UUID
    task_snapshot: TaskSnapshot
    project_root: str


class TaskUpdatedEvent(BaseEvent):
    """Event emitted when a task is updated."""

    event_type: str = "task_updated"
    task_id: UUID
    old_snapshot: TaskSnapshot
    new_snapshot: TaskSnapshot
    updated_fields: list[str]


class TaskCompletedEvent(BaseEvent):
    """Event emitted when a task is completed."""

    event_type: str = "task_completed"
    task_id: UUID
    task_snapshot: TaskSnapshot
    completion_timestamp: datetime


class TaskCancelledEvent(BaseEvent):
    """Event emitted when a task is cancelled."""

    event_type: str = "task_cancelled"
    task_id: UUID
    task_snapshot: TaskSnapshot
    reason: str | None = None
    previous_status: str


class TaskReopenedEvent(BaseEvent):
    """Event emitted when a task is reopened."""

    event_type: str = "task_reopened"
    task_id: UUID
    task_snapshot: TaskSnapshot
    previous_status: str
    new_status: str


class TaskDeletedEvent(BaseEvent):
    """Event emitted when a task is deleted."""

    event_type: str = "task_deleted"
    task_id: UUID
    task_snapshot: TaskSnapshot


class TasksImportedEvent(BaseEvent):
    """Event emitted when tasks are imported."""

    event_type: str = "tasks_imported"
    import_count: int
    skipped_count: int
    failed_count: int
    import_strategy: str
    imported_task_ids: list[UUID]
