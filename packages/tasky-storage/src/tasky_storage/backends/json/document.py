"""JSON storage document structure using plain task snapshots."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskDocument(BaseModel):
    """JSON storage document structure using plain task snapshots."""

    version: str = Field(default="1.0", description="Document version")
    tasks: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dictionary of task_id -> serialized task snapshot",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When this document was first created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When this document was last updated",
    )

    def add_task(self, task_id: str, snapshot: dict[str, Any]) -> None:
        """Add or update a serialized task in the document."""
        self.tasks[task_id] = dict(snapshot)
        self.updated_at = datetime.now(tz=UTC)

    def remove_task(self, task_id: str) -> bool:
        """Remove a serialized task from the document."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.updated_at = datetime.now(tz=UTC)
            return True
        return False

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Return a serialized task snapshot if it exists."""
        snapshot = self.tasks.get(task_id)
        return dict(snapshot) if snapshot is not None else None

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return all serialized task snapshots."""
        return [dict(snapshot) for snapshot in self.tasks.values()]

    @classmethod
    def create_empty(cls) -> TaskDocument:
        """Create a new empty task document."""
        return cls(version="1.0", tasks={})
