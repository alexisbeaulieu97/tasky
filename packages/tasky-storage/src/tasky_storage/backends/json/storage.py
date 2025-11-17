"""Filesystem-backed JSON storage helper for tasky."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
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
        is first written to a unique temporary file, flushed and synced to disk,
        then atomically renamed to the target path. This ensures that the file
        is never left in a partially written state, even if the process is
        interrupted or disk becomes full.

        The temporary file uses a unique name to prevent race conditions when
        multiple processes/threads attempt concurrent saves.
        """
        # Create unique temporary file in same directory (ensures same filesystem)
        # Using delete=False so we control cleanup, dir ensures atomic rename works
        temp_fd = None
        temp_path = None
        try:
            # Ensure parent directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_fd, temp_name = tempfile.mkstemp(
                suffix=".tmp",
                prefix=f".{self.path.name}.",
                dir=self.path.parent,
                text=False,  # Use binary mode for explicit encoding control
            )
            temp_path = Path(temp_name)

            # Write JSON data to temporary file
            # Use fdopen for proper buffering and to handle partial writes
            json_bytes = json.dumps(data, indent=2).encode("utf-8")
            with os.fdopen(temp_fd, "wb") as temp_file:
                temp_file.write(json_bytes)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            temp_fd = None  # Mark as closed (fdopen closes it)

            # Atomic rename: replaces target file atomically
            # On POSIX systems, this is atomic even if target exists
            temp_path.replace(self.path)
            temp_path = None  # Mark as successfully renamed

        except OSError as exc:
            msg = f"Failed to save storage file at {self.path}: {exc}"
            raise StorageIOError(msg, cause=exc) from exc
        except (ValueError, TypeError) as exc:
            msg = f"Failed to serialize data to JSON: {exc}"
            raise StorageDataError(msg, cause=exc) from exc
        finally:
            # Clean up temporary file descriptor if still open
            if temp_fd is not None:
                with contextlib.suppress(OSError):
                    os.close(temp_fd)
            # Clean up temporary file if it wasn't successfully renamed
            if temp_path is not None and temp_path.exists():
                with contextlib.suppress(OSError):
                    temp_path.unlink()
