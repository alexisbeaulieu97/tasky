import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, computed_field
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

logger = logging.getLogger(__name__)

DEFAULT_TASKY_DIR = Path.home() / ".tasky"
TASKY_ROOT_DIR_ENV_VAR = "TASKY_ROOT_DIR"


@lru_cache(maxsize=1)
def resolve_default_tasky_dir() -> Path:
    """
    Resolve the Tasky root directory using an environment variable first,
    defaulting to the user-scoped directory if it is not set.
    """
    env_value = os.getenv(TASKY_ROOT_DIR_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser()
    return DEFAULT_TASKY_DIR


def resolve_tasky_dir(value: Any | None = None) -> Path:
    """
    Expand and normalize Tasky directory values, falling back to the default.
    """
    if value is None:
        return resolve_default_tasky_dir()
    return Path(value).expanduser()


class JsonConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A settings source that loads variables from a JSON file
    at <tasky_dir>/config.json
    """

    _config_cache: dict[str, Any] | None = None
    _config_tasky_dir: Path | None = None

    def _load_config(self) -> dict[str, Any] | None:
        tasky_dir = resolve_tasky_dir(self.current_state.get("tasky_dir"))

        if self._config_cache is not None and tasky_dir == self._config_tasky_dir:
            return self._config_cache

        config_path = tasky_dir / "config.json"
        if not config_path.exists():
            self._config_cache = None
            self._config_tasky_dir = tasky_dir
            return None

        try:
            config_text = config_path.read_text(encoding="utf-8")
            self._config_cache = json.loads(config_text)
        except (OSError, json.JSONDecodeError) as exc:
            self._config_cache = None
            logger.warning(
                "Failed to load Tasky config from %s: %s",
                config_path,
                exc,
            )
        finally:
            self._config_tasky_dir = tasky_dir
        return self._config_cache

    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        config = self._load_config()
        if not config:
            return None, field_name, False

        field_value = config.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name,
                field,
                field_value,
                value_is_complex,
            )
            if field_value is not None:
                d[field_key] = field_value
        return d


class TaskySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TASKY_",
    )

    tasky_dir: Path = Field(
        default_factory=resolve_default_tasky_dir,
        description="Base directory for tasky configuration and storage.",
    )

    registry_backend: Literal["json", "sqlite"] = Field(
        default="json",
        description="Storage backend for the global projects registry.",
    )

    @computed_field
    def projects_dir(self) -> Path:
        return self.tasky_dir / "projects"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            JsonConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


settings = TaskySettings()


def invalidate_settings_cache() -> None:
    """
    Clear cached JSON configuration so subsequent loads read from disk.
    """
    JsonConfigSettingsSource._config_cache = None
    JsonConfigSettingsSource._config_tasky_dir = None


from tasky_core.projects import (  # noqa: E402
    ProjectAlreadyInitialisedError,
    ProjectConfig,
    ProjectContext,
    ProjectInitialisationError,
    ProjectRegistryEntry,
    ProjectRegistryError,
    ProjectSettingsError,
)

from .projects import (  # noqa: E402
    ProjectSettingsService,
    build_task_service,
    ensure_project_initialised,
    get_project_context,
    get_task_repository,
    initialise_project,
    is_project_initialised,
    list_registered_projects,
    load_project_config,
    register_project,
    prune_missing_projects,
    save_project_config,
    unregister_project,
)
from .queries import (  # noqa: E402
    ProjectOverview,
    ProjectQueryService,
)
from .repositories import TaskRepositoryFactory  # noqa: E402

__all__ = [
    "DEFAULT_TASKY_DIR",
    "TASKY_ROOT_DIR_ENV_VAR",
    "TaskySettings",
    "JsonConfigSettingsSource",
    "settings",
    "invalidate_settings_cache",
    "resolve_default_tasky_dir",
    "resolve_tasky_dir",
    # project helpers
    "ProjectConfig",
    "ProjectContext",
    "ProjectRegistryEntry",
    "ProjectRegistryError",
    "ProjectSettingsError",
    "ProjectInitialisationError",
    "ProjectAlreadyInitialisedError",
    "ProjectSettingsService",
    "TaskRepositoryFactory",
    "ProjectQueryService",
    "ProjectOverview",
    "ensure_project_initialised",
    "initialise_project",
    "is_project_initialised",
    "load_project_config",
    "save_project_config",
    "register_project",
    "prune_missing_projects",
    "unregister_project",
    "list_registered_projects",
    "get_project_context",
    "get_task_repository",
    "build_task_service",
]
