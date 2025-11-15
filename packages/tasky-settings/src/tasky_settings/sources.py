"""Custom settings sources for loading configuration from TOML files."""

import json
import logging
import tomllib
from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource

logger = logging.getLogger(__name__)


class TomlConfigSource(PydanticBaseSettingsSource):
    """Base class for loading configuration from TOML files.

    This source loads and parses TOML files, handling missing files and
    malformed TOML gracefully. Subclasses specify the file path.
    """

    def __init__(self, settings_cls: type, file_path: Path) -> None:
        """Initialize the TOML config source.

        Args:
            settings_cls: The settings class being configured
            file_path: Path to the TOML configuration file

        """
        super().__init__(settings_cls)
        self.file_path = file_path
        self._config_data: dict[str, Any] | None = None

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from the TOML file (cached).

        Returns:
            Dictionary of configuration values, or empty dict if file missing/invalid

        """
        if self._config_data is not None:
            return self._config_data

        if not self.file_path.exists():
            self._config_data = {}
            return self._config_data

        try:
            with self.file_path.open("rb") as f:
                self._config_data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            # Log warning but continue with defaults
            logger.warning(
                "Failed to load config from %s: %s. Using defaults.",
                self.file_path,
                e,
            )
            self._config_data = {}

        return self._config_data

    def __call__(self) -> dict[str, Any]:
        """Load configuration from the TOML file.

        Required by Pydantic's abstract base class.

        Returns:
            Dictionary of configuration values

        """
        return self._load_config()

    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        """Get value for a specific field from the config.

        Args:
            field: Field information (not used, but required by base class)
            field_name: Name of the field to get

        Returns:
            Tuple of (value, field_name, is_complex)

        """
        del field  # Unused, but required by base class signature
        config = self._load_config()

        # For nested fields (e.g., logging, task_defaults), return the section
        if field_name in config:
            return config[field_name], field_name, True

        return None, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,  # noqa: ANN401
        value_is_complex: bool,  # noqa: FBT001
    ) -> Any:  # noqa: ANN401
        """Prepare field value for model validation.

        Default implementation returns value unchanged. Override if custom
        transformation is needed.

        Args:
            field_name: Name of the field being prepared
            field: Field information from the model
            value: Raw value from config source
            value_is_complex: Whether value is a complex type

        Returns:
            Prepared value ready for model validation

        """
        del field_name, field, value_is_complex  # Unused
        return value


class GlobalConfigSource(TomlConfigSource):
    """Settings source for global configuration (~/.tasky/config.toml)."""

    def __init__(self, settings_cls: type) -> None:
        """Initialize global config source.

        Args:
            settings_cls: The settings class being configured

        """
        config_path = Path.home() / ".tasky" / "config.toml"
        super().__init__(settings_cls, config_path)


class ProjectConfigSource(TomlConfigSource):
    """Settings source for project configuration (.tasky/config.toml).

    Supports legacy JSON config with automatic detection and migration warning.
    """

    def __init__(self, settings_cls: type, project_root: Path | None = None) -> None:
        """Initialize project config source.

        Args:
            settings_cls: The settings class being configured
            project_root: Project root directory (defaults to current directory)

        """
        if project_root is None:
            project_root = Path.cwd()
        config_path = project_root / ".tasky" / "config.toml"
        super().__init__(settings_cls, config_path)
        self.project_root = project_root

    def _load_config(self) -> dict[str, Any]:  # noqa: C901
        """Load configuration from TOML or legacy JSON file.

        Returns:
            Dictionary of configuration values, or empty dict if file missing/invalid

        """
        if self._config_data is not None:
            return self._config_data

        # Try TOML first (preferred format)
        toml_path = self.project_root / ".tasky" / "config.toml"
        json_path = self.project_root / ".tasky" / "config.json"

        if toml_path.exists():
            # Load TOML
            try:
                with toml_path.open("rb") as f:
                    self._config_data = tomllib.load(f)
            except (OSError, tomllib.TOMLDecodeError) as e:
                logger.warning(
                    "Failed to load config from %s: %s. Using defaults.",
                    toml_path,
                    e,
                )
                self._config_data = {}
        elif json_path.exists():
            # Load legacy JSON with migration warning
            logger.warning(
                "Legacy JSON config detected at %s, will migrate to TOML format on next write",
                json_path,
            )
            try:
                with json_path.open("r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(
                    "Failed to load config from %s: %s. Using defaults.",
                    json_path,
                    e,
                )
                self._config_data = {}
        else:
            # No config file found
            self._config_data = {}

        if self._config_data is None:
            self._config_data = {}

        return self._config_data
