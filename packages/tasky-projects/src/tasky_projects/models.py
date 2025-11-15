"""Domain models for project registry."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class ProjectMetadata(BaseModel):
    """Metadata for a registered project.

    Attributes:
        name: Human-readable project name (derived from directory name)
        path: Absolute path to the project directory (parent of .tasky/)
        created_at: Timestamp when project was first registered
        last_accessed: Timestamp when project was last accessed
        tags: Optional tags for categorizing projects

    """

    name: str
    path: Path
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    tags: list[str] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def validate_path_is_absolute(cls, v: Path) -> Path:
        """Normalize path to absolute form by resolving relative paths."""
        if not v.is_absolute():
            return v.resolve()
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is a valid identifier."""
        if not v or not v.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)
        # Allow alphanumeric, hyphens, underscores, spaces
        if not all(c.isalnum() or c in "-_ " for c in v):
            msg = f"Invalid project name: {v}"
            raise ValueError(msg)
        return v.strip()


def _empty_project_list() -> list[ProjectMetadata]:
    """Provide a typed default factory for project collections."""
    return []


class ProjectRegistry(BaseModel):
    """Registry of all known projects.

    Attributes:
        projects: List of registered project metadata
        registry_version: Version of the registry format

    """

    projects: list[ProjectMetadata] = Field(default_factory=_empty_project_list)
    registry_version: str = "1.0"

    def get_by_name(self, name: str) -> ProjectMetadata | None:
        """Get project by name."""
        for project in self.projects:
            if project.name == name:
                return project
        return None

    def get_by_path(self, path: Path) -> ProjectMetadata | None:
        """Get project by path."""
        normalized_path = path.resolve()
        for project in self.projects:
            if project.path.resolve() == normalized_path:
                return project
        return None

    def add_or_update(self, project: ProjectMetadata) -> bool:
        """Add or update a project in the registry.

        Returns:
            True if project was added, False if updated

        """
        existing = self.get_by_path(project.path)
        if existing:
            # Update existing project
            existing.name = project.name
            existing.last_accessed = project.last_accessed
            existing.tags = project.tags
            return False
        # Add new project
        self.projects.append(project)
        return True

    def remove(self, path: Path) -> bool:
        """Remove a project from the registry.

        Returns:
            True if project was removed, False if not found

        """
        project = self.get_by_path(path)
        if project:
            self.projects.remove(project)
            return True
        return False
