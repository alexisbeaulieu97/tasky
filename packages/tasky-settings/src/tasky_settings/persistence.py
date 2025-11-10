from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from tasky_shared.jsonio import atomic_write_json, read_json_document

from . import TaskySettings, invalidate_settings_cache, resolve_tasky_dir

CONFIG_FILENAME = "config.json"


class ConfigPersistenceError(RuntimeError):
    """Base error raised when Tasky settings could not be persisted."""


class ConfigDecodeError(ConfigPersistenceError):
    """Raised when the settings JSON cannot be decoded."""


class ConfigRepository:
    def __init__(self, tasky_dir: Path | None = None) -> None:
        self._tasky_dir = resolve_tasky_dir(tasky_dir)
        self._path = self._tasky_dir / CONFIG_FILENAME

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> dict[str, Any]:
        try:
            return read_json_document(self.path, missing_ok=True)
        except json.JSONDecodeError as exc:
            raise ConfigDecodeError(f"Failed to decode Tasky config at {self.path}") from exc
        except OSError as exc:
            raise ConfigPersistenceError(f"Could not read Tasky config at {self.path}") from exc

    def write(self, values: Mapping[str, Any], *, indent: int = 2) -> Path:
        try:
            atomic_write_json(self.path, values, indent=indent, sort_keys=True)
        except OSError as exc:
            raise ConfigPersistenceError(f"Could not write Tasky config at {self.path}") from exc
        invalidate_settings_cache()
        return self.path


def load_settings(**overrides: Any) -> TaskySettings:
    """
    Load Tasky settings using the standard resolution flow.

    Any keyword arguments override resolved values, mirroring BaseSettings.
    """
    return TaskySettings(**overrides)


def config_path(tasky_dir: Path | None = None) -> Path:
    """Return the absolute path to the global Tasky config file."""
    return ConfigRepository(tasky_dir).path


def read_config(tasky_dir: Path | None = None) -> dict[str, Any]:
    """
    Read the raw JSON configuration dictionary.

    Returns an empty dict when the config file does not exist.
    """
    return ConfigRepository(tasky_dir).read()


def write_config(
    values: Mapping[str, Any],
    tasky_dir: Path | None = None,
    *,
    indent: int = 2,
) -> Path:
    """
    Persist the provided mapping to the Tasky config file atomically.
    """
    return ConfigRepository(tasky_dir).write(values, indent=indent)


def dump_settings_payload(settings: TaskySettings) -> dict[str, Any]:
    """
    Convert settings to a JSON-ready payload, omitting derived fields.
    """
    payload = settings.model_dump(
        mode="json",
        exclude={"tasky_dir", "projects_dir"},
    )
    return payload


def save_settings(settings: TaskySettings) -> Path:
    """
    Persist the provided TaskySettings instance to disk.
    """
    payload = dump_settings_payload(settings)
    return write_config(payload, settings.tasky_dir)
