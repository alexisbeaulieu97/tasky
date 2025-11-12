"""Configuration and wiring package for Tasky."""

from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from tasky_settings.models import AppSettings, LoggingSettings, TaskDefaultsSettings
from tasky_settings.sources import GlobalConfigSource, ProjectConfigSource

__all__ = [
    "AppSettings",
    "LoggingSettings",
    "TaskDefaultsSettings",
    "get_settings",
]


class InitSettingsSource(PydanticBaseSettingsSource):
    """Settings source for CLI overrides passed as initialization arguments."""

    def __init__(self, settings_cls: type, init_kwargs: dict[str, Any]) -> None:
        """Initialize the init settings source.

        Args:
            settings_cls: The settings class being configured
            init_kwargs: Dictionary of CLI override values

        """
        super().__init__(settings_cls)
        self.init_kwargs = init_kwargs

    def __call__(self) -> dict[str, Any]:
        """Return the init kwargs as configuration.

        Required by Pydantic's abstract base class.
        """
        return self.init_kwargs

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get value for a specific field from init kwargs.

        Args:
            field: Field information (not used, but required by base class)
            field_name: Name of the field to get

        Returns:
            Tuple of (value, field_name, is_complex)

        """
        del field  # Unused, but required by base class signature
        if field_name in self.init_kwargs:
            return self.init_kwargs[field_name], field_name, True

        return None, field_name, False


def get_settings(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> AppSettings:
    """Load application settings from hierarchical sources.

    Settings are loaded and merged with the following precedence (highest to lowest):
    1. CLI overrides (passed as parameters) - HIGHEST PRECEDENCE
    2. Environment variables (TASKY_*)
    3. Project config file (.tasky/config.toml)
    4. Global config file (~/.tasky/config.toml)
    5. Model defaults (defined in settings classes) - LOWEST PRECEDENCE

    Args:
        project_root: Project root directory for finding .tasky/config.toml.
                     Defaults to current working directory.
        cli_overrides: Dictionary of settings to override from CLI flags.
                      Takes highest precedence.

    Returns:
        Fully configured AppSettings instance

    Example:
        >>> settings = get_settings()
        >>> settings.logging.verbosity
        0

        >>> settings = get_settings(cli_overrides={"logging": {"verbosity": 2}})
        >>> settings.logging.verbosity
        2

    """
    # Create captured variables for closure
    _project_root = project_root
    _cli_overrides = cli_overrides or {}

    class ConfiguredAppSettings(AppSettings):
        """AppSettings with custom source configuration."""

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            """Customize the settings sources and their precedence order.

            Returns sources in order from HIGHEST to LOWEST precedence.
            First source wins over later sources.
            """
            del init_settings, dotenv_settings, file_secret_settings  # Unused
            # Order: CLI (highest) → Env → Project → Global (lowest)
            return (
                InitSettingsSource(settings_cls, _cli_overrides),
                env_settings,
                ProjectConfigSource(settings_cls, project_root=_project_root),
                GlobalConfigSource(settings_cls),
            )

    return ConfiguredAppSettings()
