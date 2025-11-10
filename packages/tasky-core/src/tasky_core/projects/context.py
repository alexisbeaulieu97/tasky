from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from .ports import (
    ProjectConfigReader,
    ProjectConfigStore,
    ProjectConfigWriter,
    TaskBootstrapper,
)

PROJECT_METADATA_DIR_NAME = ".tasky"
PROJECT_CONFIG_FILENAME = "config.json"
DEFAULT_TASKS_FILENAME = "tasks.json"
PROJECTS_REGISTRY_FILENAME = "projects.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectError(Exception):
    """Base error for project operations."""


class ProjectSettingsError(ProjectError):
    """Configuration errors for projects."""


class ProjectInitialisationError(ProjectSettingsError):
    """Raised when on-disk project state is missing or invalid."""


class ProjectAlreadyInitialisedError(ProjectInitialisationError):
    """Raised when attempting to initialise an existing project."""


class ProjectRegistryError(ProjectSettingsError):
    """Raised when the global registry cannot be processed."""


class ProjectConfig(BaseModel):
    version: Literal[1] = 1
    tasks_file: Path = Field(default_factory=lambda: Path(DEFAULT_TASKS_FILENAME))
    created_at: datetime = Field(default_factory=_now)


@dataclass(frozen=True)
class ProjectContext:
    project_path: Path
    metadata_dir: Path
    config_path: Path
    tasks_path: Path


def get_project_context(project_path: Path | None) -> ProjectContext:
    project = normalise_path(project_path or Path.cwd())
    metadata_dir = project / PROJECT_METADATA_DIR_NAME
    config_path = metadata_dir / PROJECT_CONFIG_FILENAME
    tasks_path = metadata_dir / DEFAULT_TASKS_FILENAME
    return ProjectContext(project, metadata_dir, config_path, tasks_path)


def ensure_project_initialised(context: ProjectContext) -> None:
    if not context.config_path.exists():
        raise ProjectInitialisationError(
            f"Project at {context.project_path} is not initialised."
        )


def load_project_config(
    target: ProjectContext | Path | None = None,
    *,
    config_store: ProjectConfigReader,
) -> ProjectConfig:
    context = target if isinstance(target, ProjectContext) else get_project_context(target)
    ensure_project_initialised(context)
    try:
        data = config_store.read_config(context)
        return ProjectConfig.model_validate(data)
    except OSError as exc:
        raise ProjectInitialisationError("Could not read project config.") from exc
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ProjectInitialisationError("Malformed project config.") from exc


def save_project_config(
    config: ProjectConfig,
    context: ProjectContext,
    *,
    config_store: ProjectConfigWriter,
) -> None:
    payload = config.model_dump(mode="json")
    try:
        config_store.write_config(context, payload)
    except OSError as exc:
        raise ProjectInitialisationError("Could not write project config.") from exc


def initialise_project(
    project_path: Path,
    *,
    force: bool = False,
    config_store: ProjectConfigStore,
    task_bootstrapper: TaskBootstrapper,
) -> ProjectContext:
    context = get_project_context(project_path)
    if context.config_path.exists() and not force:
        raise ProjectAlreadyInitialisedError("Project already initialised.")
    config = ProjectConfig()
    save_project_config(config, context, config_store=config_store)
    tasks_path = _resolve_tasks_path(context, config)
    task_bootstrapper.initialise_tasks(tasks_path, force=force)
    return context


def _resolve_tasks_path(context: ProjectContext, config: ProjectConfig) -> Path:
    target = config.tasks_file
    if not target.is_absolute():
        target = context.metadata_dir / target
    return target


def normalise_path(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)
