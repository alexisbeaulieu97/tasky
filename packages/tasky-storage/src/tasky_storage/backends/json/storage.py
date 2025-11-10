import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from tasky_storage.errors import StorageDataError


class TaskyJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, UUID, and enum objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class JsonStorage(BaseModel):
    """Filesystem-backed JSON storage helper."""

    path: Path

    def initialize(self, template: dict[str, Any]) -> None:
        """Create the storage file with a template if it does not already exist."""
        if not self.path.exists():
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(
                    json.dumps(template, indent=2, cls=TaskyJSONEncoder),
                    encoding="utf-8",
                )
            except (OSError, ValueError, TypeError) as exc:
                raise StorageDataError(f"Failed to initialize storage: {exc}") from exc

    def load(self) -> dict[str, Any]:
        """Load and return the persisted JSON document."""
        try:
            content = self.path.read_text(encoding="utf-8")
            return json.loads(content)
        except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
            raise StorageDataError(f"Failed to load storage: {exc}") from exc

    def save(self, data: dict[str, Any]) -> None:
        """Serialize and persist the provided document."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(data, indent=2, cls=TaskyJSONEncoder),
                encoding="utf-8",
            )
        except (OSError, ValueError, TypeError) as exc:
            raise StorageDataError(f"Failed to save storage: {exc}") from exc
