"""Project configuration models and persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


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
        """Load configuration from a JSON file.

        Args:
            path: Path to the configuration file

        Returns:
            ProjectConfig instance loaded from file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist

        """
        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise FileNotFoundError(msg)

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.model_validate(data)

    def to_file(self, path: Path) -> None:
        """Save configuration to a JSON file.

        Creates parent directories if they don't exist.

        Args:
            path: Path where configuration should be saved

        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
