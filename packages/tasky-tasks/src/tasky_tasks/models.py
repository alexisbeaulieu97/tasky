"""Models for the Tasky Tasks package."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskModel(BaseModel):
    """A model representing a task in the task management system."""

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
        default_factory=datetime.now,
        description="The date and time the task was created.",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="The date and time the task was updated.",
    )
