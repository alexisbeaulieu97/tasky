"""Models for the Tasky Tasks package."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskModel(BaseModel):
    """A model representing a task in the task management system.

    Tasks automatically track creation and modification times using UTC
    timestamps. The created_at timestamp is set once at creation, while
    updated_at is refreshed whenever mark_updated() is called.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    task_id: UUID = Field(
        default_factory=uuid4,
        description="The ID of the task.",
    )
    name: str = Field(
        ...,
        description="The name of the task.",
    )
    details: str = Field(
        ...,
        description="The details of the task.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="The status of the task.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The date and time the task was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The date and time the task was updated.",
    )

    @model_validator(mode="after")
    def _sync_initial_timestamps(self) -> TaskModel:
        """Ensure updated_at equals created_at when task is first created.

        This validator runs after model initialization and sets updated_at to
        match created_at if updated_at was not explicitly provided, ensuring
        both timestamps start with the same UTC value.
        """
        if "updated_at" not in self.model_fields_set:
            self.updated_at = self.created_at
        return self

    def mark_updated(self) -> None:
        """Refresh the updated_at timestamp to the current UTC time."""
        self.updated_at = datetime.now(tz=UTC)
