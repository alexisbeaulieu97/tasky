from __future__ import annotations

from pathlib import Path
from typing import Callable

from tasky_core import TaskService
from tasky_settings import (
    ProjectQueryService,
    ProjectSettingsService,
)

TaskServiceFactory = Callable[[Path | None], TaskService]
ProjectQueryServiceFactory = Callable[[], ProjectQueryService]


class DependencyContainer:
    def __init__(self) -> None:
        self._settings_factory: Callable[[], ProjectSettingsService] = ProjectSettingsService
        self._settings_instance: ProjectSettingsService | None = None
        self.task_service_factory: TaskServiceFactory = self._default_task_service_factory
        self.project_query_service_factory: ProjectQueryServiceFactory = (
            self._default_project_query_service_factory
        )

    def _default_task_service_factory(self, project_path: Path | None = None) -> TaskService:
        return self.settings_service().build_task_service(project_path)

    def _default_project_query_service_factory(self) -> ProjectQueryService:
        return ProjectQueryService(self.settings_service())

    def task_service(self, project_path: Path | None = None) -> TaskService:
        return self.task_service_factory(project_path)

    def project_query_service(self) -> ProjectQueryService:
        return self.project_query_service_factory()

    def settings_service(self) -> ProjectSettingsService:
        if self._settings_instance is None:
            self._settings_instance = self._settings_factory()
        return self._settings_instance

    def configure(
        self,
        *,
        task_service_factory: TaskServiceFactory | None = None,
        project_query_service_factory: ProjectQueryServiceFactory | None = None,
        settings_service_factory: Callable[[], ProjectSettingsService] | None = None,
    ) -> None:
        if settings_service_factory is not None:
            self._settings_factory = settings_service_factory
            self._settings_instance = None
        if task_service_factory is not None:
            self.task_service_factory = task_service_factory
        if project_query_service_factory is not None:
            self.project_query_service_factory = project_query_service_factory

    def reset(self) -> None:
        self._settings_factory = ProjectSettingsService
        self._settings_instance = None
        self.task_service_factory = self._default_task_service_factory
        self.project_query_service_factory = self._default_project_query_service_factory


container = DependencyContainer()


def get_task_service(project_path: Path | None = None) -> TaskService:
    return container.task_service(project_path)


def get_project_query_service() -> ProjectQueryService:
    return container.project_query_service()


def get_settings_service() -> ProjectSettingsService:
    return container.settings_service()


def configure_dependencies(
    *,
    task_service_factory: TaskServiceFactory | None = None,
    project_query_service_factory: ProjectQueryServiceFactory | None = None,
    settings_service_factory: Callable[[], ProjectSettingsService] | None = None,
) -> None:
    """
    Override dependency factories for CLI commands (useful in tests).
    """
    container.configure(
        task_service_factory=task_service_factory,
        project_query_service_factory=project_query_service_factory,
        settings_service_factory=settings_service_factory,
    )


def reset_dependencies() -> None:
    """Restore default dependency factories."""
    container.reset()
