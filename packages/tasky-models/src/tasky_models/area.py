from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .project import Project
from .task import Task


class Area(BaseModel):
    area_id: UUID = Field(
        default_factory=uuid4,
        description="The unique identifier for the area",
    )
    name: str = Field(
        ...,
        description="The name of the area",
    )
    description: str = Field(
        ...,
        description="The description of the area",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the area was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The date and time the area was last updated",
    )
    projects: list[Project] = Field(
        default_factory=list,
        description="The projects of the area",
    )
    tasks: list[Task] = Field(
        default_factory=list,
        description="The tasks of the area",
    )
