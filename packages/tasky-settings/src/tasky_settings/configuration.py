"""Settings loading helpers for Tasky configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from tasky_settings.models import AppSettings
from tasky_settings.sources import GlobalConfigSource, ProjectConfigSource


class InitSettingsSource(PydanticBaseSettingsSource):
    """Settings source for CLI overrides passed as initialization arguments."""

    def __init__(self, settings_cls: type, init_kwargs: dict[str, Any]) -> None:
        """Store initialization overrides for later retrieval."""
        super().__init__(settings_cls)
        self.init_kwargs = init_kwargs

    def __call__(self) -> dict[str, Any]:
        """Return the CLI override dictionary."""
        return self.init_kwargs

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Return a value for ``field_name`` if it exists in CLI overrides."""
        del field  # Required by abstract signature but unused
        if field_name in self.init_kwargs:
            return self.init_kwargs[field_name], field_name, True
        return None, field_name, False


def get_settings(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AppSettings:
    """Load application settings from hierarchical sources.

    Settings precedence (highest to lowest): CLI overrides, environment variables,
    project config file, global config file, and finally model defaults.
    """

    _project_root = project_root
    _cli_overrides = cli_overrides or {}

    class ConfiguredAppSettings(AppSettings):
        """AppSettings subclass with customized source ordering."""

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            """Configure settings source precedence from highest to lowest."""

            del init_settings, dotenv_settings, file_secret_settings
            return (
                InitSettingsSource(settings_cls, _cli_overrides),
                env_settings,
                ProjectConfigSource(settings_cls, project_root=_project_root),
                GlobalConfigSource(settings_cls),
            )

    return ConfiguredAppSettings()

