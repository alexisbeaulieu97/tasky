"""Filesystem-backed JSON storage helper for tasky."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from tasky_storage.errors import StorageDataError, StorageIOError


class JsonStorage(BaseModel):
    """Filesystem-backed JSON storage helper."""

    path: Path

    def initialize(self, template: dict[str, Any]) -> None:
        """Create the storage file with a template if it does not already exist.

        The template should already be JSON-serializable (e.g., from Pydantic's
        model_dump(mode='json')).
        """
        if not self.path.exists():
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(
                    json.dumps(template, indent=2),
                    encoding="utf-8",
                )
            except OSError as exc:
                msg = f"Failed to initialize storage file at {self.path}: {exc}"
                raise StorageIOError(msg, cause=exc) from exc
            except (ValueError, TypeError) as exc:
                msg = f"Failed to serialize template data: {exc}"
                raise StorageDataError(msg, cause=exc) from exc

    def load(self) -> dict[str, Any]:
        """Load and return the persisted JSON document."""
        try:
            content = self.path.read_text(encoding="utf-8")
            return json.loads(content)
        except (FileNotFoundError, OSError) as exc:
            msg = f"Failed to load storage file at {self.path}: {exc}"
            raise StorageIOError(msg, cause=exc) from exc
        except (ValueError, TypeError) as exc:
            msg = f"Failed to parse JSON content from {self.path}: {exc}"
            raise StorageDataError(msg, cause=exc) from exc

    def save(self, data: dict[str, Any]) -> None:
        """Serialize and persist the provided document.

        The data should already be JSON-serializable (e.g., from Pydantic's
        model_dump(mode='json')).
        """
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            msg = f"Failed to save storage file at {self.path}: {exc}"
            raise StorageIOError(msg, cause=exc) from exc
        except (ValueError, TypeError) as exc:
            msg = f"Failed to serialize data to JSON: {exc}"
            raise StorageDataError(msg, cause=exc) from exc
