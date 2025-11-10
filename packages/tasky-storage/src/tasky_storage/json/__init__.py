from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Protocol

from tasky_shared.jsonio import atomic_write_json
from tasky_storage.errors import StorageDataError

Document = dict[str, Any]


class DocumentSerializer(Protocol):
    def loads(self, payload: str) -> Document: ...

    def dumps(self, document: Mapping[str, Any]) -> str: ...


class JsonDocumentSerializer(DocumentSerializer):
    def loads(self, payload: str) -> Document:
        try:
            data = json.loads(payload) if payload.strip() else {}
        except json.JSONDecodeError as exc:
            raise StorageDataError("Malformed JSON payload.") from exc
        if not isinstance(data, dict):
            raise StorageDataError("Storage payload must be a JSON object.")
        return dict(data)

    def dumps(self, document: Mapping[str, Any]) -> str:
        serialisable = dict(document)
        try:
            return json.dumps(serialisable, indent=2, sort_keys=True) + "\n"
        except (TypeError, ValueError) as exc:
            raise StorageDataError("Document contains non-serialisable data.") from exc


class FileDocumentGateway:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    @property
    def path(self) -> Path:
        return self._file_path

    def read(self) -> str | None:
        if not self.path.exists():
            return None
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageDataError(
                f"Could not read storage file: {self.path}"
            ) from exc

    def write(self, content: str | Mapping[str, Any]) -> None:
        try:
            atomic_write_json(self.path, content)
        except OSError as exc:
            raise StorageDataError(
                f"Could not write storage file: {self.path}"
            ) from exc


class JsonDocumentStore:
    """Minimal JSON-backed store that reads and writes a single document."""

    def __init__(
        self,
        file_path: str | Path,
        *,
        serializer: DocumentSerializer | None = None,
        gateway: FileDocumentGateway | None = None,
    ) -> None:
        path = Path(file_path).expanduser()
        if path.is_dir():
            raise StorageDataError(f"Expected file path, received directory: {path}")
        self._serializer = serializer or JsonDocumentSerializer()
        self._gateway = gateway or FileDocumentGateway(path)

    def load(self) -> Document:
        """Load the entire document. Missing files yield an empty dictionary."""
        raw = self._gateway.read()
        if raw is None:
            return {}
        try:
            return self._serializer.loads(raw)
        except StorageDataError as exc:
            raise StorageDataError(
                f"Malformed JSON in {self._gateway.path}"
            ) from exc

    def save(self, document: Mapping[str, Any]) -> None:
        """Persist the provided document, overwriting any previous content."""
        payload = self._serializer.dumps(document)
        self._gateway.write(payload)
