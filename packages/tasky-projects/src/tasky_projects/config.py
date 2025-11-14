"""Project configuration models and persistence."""

from __future__ import annotations

import json
import logging
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import tomli_w
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StorageConfig(BaseModel):
    """Storage backend configuration.

    Attributes:
        backend: Name of the storage backend (e.g., "json", "sqlite")
        path: Relative path from .tasky/ directory to storage file

    """

    backend: str = "json"
    path: str = "tasks.json"


class ProjectConfig(BaseModel):
    """Project-level configuration.

    Attributes:
        version: Configuration schema version
        storage: Storage backend configuration
        created_at: Timestamp when project was initialized

    """

    version: str = "1.0"
    storage: StorageConfig = Field(default_factory=StorageConfig)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @classmethod
    def from_file(cls, path: Path) -> ProjectConfig:
        """Load configuration from a TOML file.

        Supports legacy JSON format with automatic detection and migration warning.

        Args:
            path: Path to the configuration file (.tasky/config.toml or .tasky/config.json)

        Returns:
            ProjectConfig instance loaded from file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist

        """
        # Try TOML first (preferred format)
        toml_path = path.parent / "config.toml"
        json_path = path.parent / "config.json"

        # If specific path provided, use it
        if path.exists():
            if path.suffix == ".json":
                logger.warning(
                    "Legacy JSON config detected at %s, will migrate to TOML format on next write",
                    path,
                )
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.model_validate(data)
            # Assume TOML
            with path.open("rb") as f:
                data = tomllib.load(f)
            return cls.model_validate(data)

        # Auto-detect if path doesn't exist
        if toml_path.exists():
            with toml_path.open("rb") as f:
                data = tomllib.load(f)
            return cls.model_validate(data)
        if json_path.exists():
            logger.warning(
                "Legacy JSON config detected at %s, will migrate to TOML format on next write",
                json_path,
            )
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.model_validate(data)
        msg = f"Configuration file not found: {path}"
        raise FileNotFoundError(msg)

    def to_file(self, path: Path) -> None:
        """Save configuration to a TOML file.

        Creates parent directories if they don't exist.
        Always writes in TOML format regardless of input format.

        Args:
            path: Path where configuration should be saved

        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure we always write TOML format
        if path.suffix != ".toml":
            path = path.parent / "config.toml"

        with path.open("wb") as f:
            tomli_w.dump(self.model_dump(mode="json"), f)
