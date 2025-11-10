from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Task(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    task_id: UUID = Field(
        default_factory=uuid4,
        description="The unique identifier for the task",
    )
    name: str = Field(
        ...,
        description="The name of the task",
    )
    details: str = Field(
        ...,
        description="The description of the task",
    )
    completed: bool = Field(
        default=False,
        description="Whether the task is completed",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the task was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the task was last updated",
    )
    subtasks: list[Self] = Field(
        default_factory=list,
        description="The subtasks of the task",
    )

    @classmethod
    def create(
        cls,
        *,
        name: str,
        details: str,
        completed: bool = False,
        task_id: UUID | None = None,
        subtasks: Iterable[Task] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> Task:
        """
        Factory helper that enforces sanitization and timestamp invariants.
        """
        raw_timestamp = clock() if clock is not None else datetime.now(timezone.utc)
        timestamp = _ensure_utc(raw_timestamp)
        payload = {
            "name": name,
            "details": details,
            "completed": completed,
            "created_at": timestamp,
            "updated_at": timestamp,
            "subtasks": list(subtasks or []),
        }
        if task_id is not None:
            payload["task_id"] = task_id
        return cls(**payload)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return _normalize_name(value)

    @field_validator("details")
    @classmethod
    def _validate_details(cls, value: str) -> str:
        return _normalize_details(value)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: datetime | str | None) -> datetime | None:
        if value is None:
            return value
        if isinstance(value, str):
            value = _parse_datetime(value)
        return _ensure_utc(value)

    def add_subtask(self, subtask: Task) -> None:
        self.subtasks.append(subtask)
        self.touch()

    def remove_subtask(self, identifier: UUID) -> bool:
        before = len(self.subtasks)
        self.subtasks = [task for task in self.subtasks if task.task_id != identifier]
        removed = len(self.subtasks) != before
        if removed:
            self.touch()
        return removed

    def mark_complete(self) -> None:
        self.completed = True
        self.touch()

    def mark_incomplete(self) -> None:
        self.completed = False
        self.touch()

    def update_content(self, *, name: str | None = None, details: str | None = None) -> None:
        """
        Update user-facing fields, ensuring sanitization + timestamp refresh.
        """
        changed = self._apply_name_update(name)
        changed = self._apply_details_update(details) or changed
        if changed:
            self.touch()

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def _apply_name_update(self, value: str | None) -> bool:
        if value is None:
            return False
        normalized = _normalize_name(value)
        if normalized == self.name:
            return False
        self.name = normalized
        return True

    def _apply_details_update(self, value: str | None) -> bool:
        if value is None:
            return False
        normalized = _normalize_details(value)
        if normalized == self.details:
            return False
        self.details = normalized
        return True


def _normalize_name(value: str) -> str:
    if value is None:
        raise ValueError("Task name cannot be blank.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Task name cannot be blank.")
    return normalized


def _normalize_details(value: str) -> str:
    if value is None:
        raise ValueError("Task details cannot be blank.")
    normalized = value.strip()
    if not normalized:
        raise ValueError("Task details cannot be blank.")
    return normalized


def _ensure_utc(timestamp: datetime) -> datetime:
    value = timestamp
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("Timestamps must be ISO 8601 strings.") from exc
