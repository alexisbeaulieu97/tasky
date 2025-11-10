from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping, Protocol

from tasky_storage.errors import StorageDataError

Document = dict[str, Any]


class RowSerializer(Protocol):
    def loads(self, payload: str) -> Document: ...

    def dumps(self, document: Mapping[str, Any]) -> str: ...


class JsonRowSerializer(RowSerializer):
    def loads(self, payload: str) -> Document:
        try:
            data = json.loads(payload) if payload else {}
        except json.JSONDecodeError as exc:
            raise StorageDataError("Malformed JSON payload in SQLite store.") from exc
        if not isinstance(data, dict):
            raise StorageDataError("Storage payload must be a JSON object.")
        return dict(data)

    def dumps(self, document: Mapping[str, Any]) -> str:
        serialisable = dict(document)
        try:
            return json.dumps(serialisable, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise StorageDataError("Document contains non-serialisable data.") from exc


class SQLiteDocumentStore:
    """
    SQLite-based document store that persists a single JSON object.
    """

    def __init__(
        self,
        database_path: str | Path,
        *,
        serializer: RowSerializer | None = None,
        table_name: str = "documents",
        key: str = "tasks",
    ) -> None:
        self._path = Path(database_path).expanduser()
        self._serializer = serializer or JsonRowSerializer()
        self._table = table_name
        self._key = key
        self._ensure_schema()

    def load(self) -> Document:
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"SELECT payload FROM {self._table} WHERE document_key = ?",
                (self._key,),
            )
            row = cursor.fetchone()
            if row is None:
                return {}
            payload = row["payload"]
            return self._serializer.loads(payload)

    def save(self, document: Mapping[str, Any]) -> None:
        payload = self._serializer.dumps(document)
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                f"""
                INSERT INTO {self._table} (document_key, payload)
                VALUES (?, ?)
                ON CONFLICT(document_key)
                DO UPDATE SET payload = excluded.payload
                """,
                (self._key, payload),
            )
            conn.commit()

    def _ensure_schema(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    document_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()
