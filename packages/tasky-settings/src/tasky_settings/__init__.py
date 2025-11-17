"""Configuration and wiring package for Tasky."""

from pathlib import Path

from tasky_projects.registry import ProjectRegistryService

from tasky_settings.backend_registry import BackendFactory, BackendRegistry, registry
from tasky_settings.configuration import get_settings
from tasky_settings.factory import ProjectNotFoundError, create_task_service, find_project_root
from tasky_settings.models import (
    AppSettings,
    LoggingSettings,
    ProjectRegistrySettings,
    StorageSettings,
    TaskDefaultsSettings,
)

__all__ = [
    "AppSettings",
    "BackendFactory",
    "BackendRegistry",
    "LoggingSettings",
    "ProjectNotFoundError",
    "ProjectRegistrySettings",
    "StorageSettings",
    "TaskDefaultsSettings",
    "create_task_service",
    "find_project_root",
    "get_project_registry_service",
    "get_settings",
    "registry",
]


def get_project_registry_service() -> ProjectRegistryService:
    """Create and return a ProjectRegistryService instance.

    This factory creates a registry service configured with the
    registry_path from the application settings.

    Returns:
        ProjectRegistryService: A configured registry service instance.

    Raises:
        ValueError: If project_registry settings are missing or invalid.

    """
    settings = get_settings()
    project_registry: ProjectRegistrySettings | None = getattr(
        settings,
        "project_registry",
        None,
    )

    if project_registry is None:
        msg = "Project registry settings not configured"
        raise ValueError(msg)

    if not project_registry.registry_path:
        msg = "Project registry path not configured"
        raise ValueError(msg)

    return ProjectRegistryService(project_registry.registry_path)
