from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .task import Task


class Project(BaseModel):
    project_id: UUID = Field(
        default_factory=uuid4,
        description="The unique identifier for the project",
    )
    name: str = Field(
        ...,
        description="The name of the project",
    )
    description: str = Field(
        ...,
        description="The description of the project",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the project was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the project was last updated",
    )
    tasks: list[Task] = Field(
        default_factory=list,
        description="The tasks of the project",
    )
