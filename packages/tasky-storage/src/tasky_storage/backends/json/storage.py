"""Filesystem-backed JSON storage helper for tasky."""

from __future__ import annotations

import contextlib
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
        """Serialize and persist the provided document using atomic writes.

        The data should already be JSON-serializable (e.g., from Pydantic's
        model_dump(mode='json')).

        This method uses atomic writes to prevent data corruption: the data
        is first written to a temporary file, then atomically renamed to the
        target path. This ensures that the file is never left in a partially
        written state, even if the process is interrupted or disk becomes full.
        """
        # Write to temporary file in same directory (ensures same filesystem)
        temp_path = self.path.with_suffix(".tmp")

        try:
            # Ensure parent directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file
            temp_path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )

            # Atomic rename: replaces target file atomically
            # On POSIX systems, this is atomic even if target exists
            temp_path.replace(self.path)

        except OSError as exc:
            msg = f"Failed to save storage file at {self.path}: {exc}"
            # Clean up temporary file if it exists
            if temp_path.exists():
                with contextlib.suppress(OSError):
                    temp_path.unlink()
            raise StorageIOError(msg, cause=exc) from exc
        except (ValueError, TypeError) as exc:
            msg = f"Failed to serialize data to JSON: {exc}"
            # Clean up temporary file if it exists
            if temp_path.exists():
                with contextlib.suppress(OSError):
                    temp_path.unlink()
            raise StorageDataError(msg, cause=exc) from exc
