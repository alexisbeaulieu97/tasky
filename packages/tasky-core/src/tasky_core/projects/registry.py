from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .context import (
    ProjectRegistryError,
    get_project_context,
    normalise_path,
)

def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectRegistryEntry(BaseModel):
    project_id: UUID = Field(default_factory=uuid4)
    path: Path
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    total_tasks: int | None = None
    completed_tasks: int | None = None
    progress_updated_at: datetime | None = None

    def touch(self) -> None:
        self.updated_at = _now()

    def set_progress(self, *, total_tasks: int, completed_tasks: int) -> None:
        self.total_tasks = total_tasks
        self.completed_tasks = completed_tasks
        self.progress_updated_at = _now()
        self.touch()


RegistryBackend = Literal["json", "sqlite"]


class ProjectRegistry(BaseModel):
    version: Literal[1] = 1
    projects: list[ProjectRegistryEntry] = Field(default_factory=list)

    def find(self, path: Path) -> ProjectRegistryEntry | None:
        target = normalise_path(path)
        for entry in self.projects:
            if normalise_path(entry.path) == target:
                return entry
        return None

    def upsert(self, entry: ProjectRegistryEntry) -> None:
        existing = self.find(entry.path)
        if existing is None:
            self.projects.append(entry)
        else:
            existing.path = entry.path
            existing.touch()

    def remove(self, path: Path) -> bool:
        before = len(self.projects)
        target = normalise_path(path)
        self.projects = [
            entry for entry in self.projects if normalise_path(entry.path) != target
        ]
        return len(self.projects) != before


class ProjectRegistryRepository(Protocol):
    def load(self) -> ProjectRegistry: ...

    def save(self, registry: ProjectRegistry) -> None: ...


def register_project(
    project_path: Path,
    *,
    repository: ProjectRegistryRepository,
) -> ProjectRegistryEntry:
    registry = repository.load()
    entry = registry.find(project_path)
    if entry is None:
        entry = ProjectRegistryEntry(path=normalise_path(project_path))
        registry.projects.append(entry)
    entry.touch()
    repository.save(registry)
    return entry


def unregister_project(
    project_path: Path,
    *,
    repository: ProjectRegistryRepository,
) -> None:
    registry = repository.load()
    removed = registry.remove(project_path)
    if not removed:
        raise ProjectRegistryError(f"Project at {project_path} is not registered.")
    repository.save(registry)


def list_registered_projects(
    repository: ProjectRegistryRepository,
    *,
    include_missing: bool = False,
) -> Iterable[ProjectRegistryEntry]:
    registry = repository.load()
    if include_missing:
        return list(registry.projects)
    entries: list[ProjectRegistryEntry] = []
    for entry in registry.projects:
        context = get_project_context(entry.path)
        if (
            context.project_path.exists()
            and context.metadata_dir.exists()
            and context.config_path.exists()
        ):
            entries.append(entry)
    return entries


def prune_missing_projects(
    repository: ProjectRegistryRepository,
) -> list[ProjectRegistryEntry]:
    registry = repository.load()
    removed: list[ProjectRegistryEntry] = []
    kept: list[ProjectRegistryEntry] = []
    for entry in registry.projects:
        context = get_project_context(entry.path)
        if (
            context.project_path.exists()
            and context.metadata_dir.exists()
            and context.config_path.exists()
        ):
            kept.append(entry)
        else:
            removed.append(entry)
    if removed:
        registry.projects = kept
        repository.save(registry)
    return removed


def update_project_progress(
    project_path: Path,
    *,
    total_tasks: int,
    completed_tasks: int,
    repository: ProjectRegistryRepository,
) -> ProjectRegistryEntry:
    registry = repository.load()
    entry = registry.find(project_path)
    if entry is None:
        raise ProjectRegistryError(f"Project at {project_path} is not registered.")
    entry.set_progress(total_tasks=total_tasks, completed_tasks=completed_tasks)
    repository.save(registry)
    return entry
