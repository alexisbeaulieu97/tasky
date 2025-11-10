from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tasky_core import TaskUseCaseError, count_tasks
from tasky_core.projects import (
    ProjectInitialisationError,
    ProjectRegistryEntry,
    ProjectRegistryError,
)

from .projects import ProjectSettingsService


@dataclass(frozen=True)
class ProjectOverview:
    entry: ProjectRegistryEntry
    exists: bool
    progress: tuple[int, int] | None

    @property
    def path(self) -> Path:
        return Path(self.entry.path)


class ProjectQueryService:
    def __init__(self, settings_service: ProjectSettingsService | None = None) -> None:
        self._settings = settings_service or ProjectSettingsService()

    def list_overviews(
        self,
        *,
        include_missing: bool = False,
        refresh_cache: bool = False,
    ) -> list[ProjectOverview]:
        overviews: list[ProjectOverview] = []
        for entry in self._settings.list_registered_projects(include_missing=True):
            overview = self._build_overview(entry, include_missing, refresh_cache)
            if overview is not None:
                overviews.append(overview)
        return overviews

    def _build_overview(
        self,
        entry: ProjectRegistryEntry,
        include_missing: bool,
        refresh_cache: bool,
    ) -> ProjectOverview | None:
        path = Path(entry.path)
        exists = self._project_exists(path)
        if not include_missing and not exists:
            return None
        progress = self._resolve_progress(
            entry=entry,
            path=path,
            exists=exists,
            refresh_cache=refresh_cache,
        )
        return ProjectOverview(entry=entry, exists=exists, progress=progress)

    def _resolve_progress(
        self,
        *,
        entry: ProjectRegistryEntry,
        path: Path,
        exists: bool,
        refresh_cache: bool,
    ) -> tuple[int, int] | None:
        if not exists:
            return None
        if not refresh_cache:
            cached = self._cached_progress(entry)
            if cached is not None:
                return cached
        return self._project_progress(path)

    def _project_exists(self, path: Path) -> bool:
        context = self._settings.get_project_context(path)
        return context.project_path.exists() and context.config_path.exists()

    def _project_progress(self, path: Path) -> tuple[int, int] | None:
        try:
            refreshed = self._settings.refresh_project_progress(path)
        except ProjectRegistryError:
            return None
        if refreshed is None:
            try:
                service = self._settings.build_task_service(path)
                tasks = service.list()
            except (ProjectInitialisationError, ProjectRegistryError, TaskUseCaseError):
                return None
            return count_tasks(tasks)
        return refreshed

    def _cached_progress(
        self,
        entry: ProjectRegistryEntry,
    ) -> tuple[int, int] | None:
        if entry.total_tasks is None or entry.completed_tasks is None:
            return None
        total = entry.total_tasks
        completed = entry.completed_tasks
        remaining = max(total - completed, 0)
        return (remaining, total)
