from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol
from uuid import UUID

import json
import sqlite3

from pydantic import ValidationError

from tasky_core.repositories import TaskRepository, TaskRepositoryError
from tasky_models import Task

from .errors import StorageDataError
from .json import JsonDocumentStore


class DocumentStore(Protocol):
    def load(self) -> dict: ...

    def save(self, document: Mapping[str, Any]) -> None: ...


class JsonTaskRepository(TaskRepository):
    """Task repository implementation backed by a JsonDocumentStore."""

    def __init__(
        self,
        store: DocumentStore,
        collection: str = "tasks",
    ) -> None:
        self._store = store
        self._collection = collection
        self._serializer = _TaskSerializer()

    def list_tasks(self) -> list[Task]:
        collection = self._load_task_collection()
        return list(collection.tasks)

    def upsert_task(self, task: Task) -> Task:
        collection = self._load_task_collection()
        tasks = collection.tasks
        desired = _normalise_id(task.task_id)
        updated: list[Task] = []
        replaced = False
        for existing in tasks:
            if _normalise_id(existing.task_id) == desired:
                updated.append(task)
                replaced = True
            else:
                updated.append(existing)
        if not replaced:
            updated.append(task)
        collection.tasks = updated
        self._save_task_collection(collection)
        return task

    def delete_task(self, task_id: str | UUID) -> None:
        desired = _normalise_id(task_id)
        collection = self._load_task_collection()
        tasks = collection.tasks
        retained = [task for task in tasks if _normalise_id(task.task_id) != desired]
        if len(retained) == len(tasks):
            raise TaskRepositoryError(f"Task '{desired}' not found.")
        collection.tasks = retained
        self._save_task_collection(collection)

    def replace_tasks(self, tasks: Iterable[Task]) -> None:
        collection = _TaskCollection(document=self._load_document(), tasks=list(tasks))
        self._save_task_collection(collection)

    def _load_task_collection(self) -> _TaskCollection:
        document = self._load_document()
        payload = self._extract_collection(document)
        tasks: list[Task] = []
        for entry in payload:
            tasks.append(self._serializer.load(entry))
        return _TaskCollection(document=document, tasks=tasks)

    def _extract_collection(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        payload = document.get(self._collection, [])
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise TaskRepositoryError(
                f"Collection '{self._collection}' must be stored as a list."
            )
        normalised: list[dict[str, Any]] = []
        for entry in payload:
            if not isinstance(entry, dict):
                raise TaskRepositoryError("Each stored task must be a JSON object.")
            normalised.append(entry)
        return normalised

    def _load_document(self) -> dict:
        try:
            return self._store.load()
        except StorageDataError as exc:
            raise TaskRepositoryError("Failed to load tasks document.") from exc

    def _save_task_collection(self, collection: _TaskCollection) -> None:
        collection.document[self._collection] = [
            self._serializer.dump(task) for task in collection.tasks
        ]
        self._save_document(collection.document)

    def _save_document(self, document: dict) -> None:
        try:
            self._store.save(document)
        except StorageDataError as exc:
            raise TaskRepositoryError("Failed to persist tasks document.") from exc


def build_json_task_repository(file_path: Path) -> JsonTaskRepository:
    """Factory for a JsonTaskRepository pointing at the given file."""
    store = JsonDocumentStore(file_path)
    return JsonTaskRepository(store=store)


class SQLiteTaskRepository(TaskRepository):
    """Task repository implementation backed by a normalized SQLite schema."""

    def __init__(self, database_path: Path) -> None:
        self._path = Path(database_path).expanduser()
        self._ensure_schema()

    def list_tasks(self) -> list[Task]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT task_id, name, details, completed, created_at, updated_at, parent_id, position
                FROM tasks
                ORDER BY parent_id IS NULL DESC, parent_id, position
                """
            )
            rows = cursor.fetchall()
        by_id: dict[str, Task] = {}
        children: dict[str | None, list[str]] = {}
        for row in rows:
            task = _row_to_task(row)
            by_id[str(task.task_id)] = task
            parent = row["parent_id"]
            children.setdefault(parent, []).append(str(task.task_id))
        roots: list[Task] = []
        for task_id in children.get(None, []):
            roots.append(_attach_children(task_id, by_id, children))
        return roots

    def upsert_task(self, task: Task) -> Task:
        with self._transaction() as conn:
            existing = conn.execute(
                "SELECT position FROM tasks WHERE task_id = ?", (str(task.task_id),)
            ).fetchone()
            if existing is None:
                position = self._next_position(conn, None)
            else:
                position = existing["position"]
                conn.execute("DELETE FROM tasks WHERE task_id = ?", (str(task.task_id),))
            self._insert_task(conn, task, parent_id=None, position=position)
        return task

    def delete_task(self, task_id: str | UUID) -> None:
        identifier = str(task_id)
        with self._transaction() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE task_id = ?", (identifier,))
            if cursor.rowcount == 0:
                raise TaskRepositoryError(f"Task '{identifier}' not found.")

    def replace_tasks(self, tasks: Iterable[Task]) -> None:
        roots = list(tasks)
        with self._transaction() as conn:
            conn.execute("DELETE FROM tasks")
            for position, task in enumerate(roots):
                self._insert_task(conn, task, parent_id=None, position=position)

    def _insert_task(
        self,
        conn: sqlite3.Connection,
        task: Task,
        *,
        parent_id: str | None,
        position: int,
    ) -> None:
        payload = _task_to_row(task, parent_id=parent_id, position=position)
        conn.execute(
            """
            INSERT INTO tasks (
                task_id, name, details, completed, created_at, updated_at, parent_id, position
            )
            VALUES (:task_id, :name, :details, :completed, :created_at, :updated_at, :parent_id, :position)
            """,
            payload,
        )
        for index, child in enumerate(task.subtasks):
            self._insert_task(
                conn,
                child,
                parent_id=str(task.task_id),
                position=index,
            )

    def _next_position(self, conn: sqlite3.Connection, parent_id: str | None) -> int:
        if parent_id is None:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM tasks WHERE parent_id IS NULL"
            )
        else:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM tasks WHERE parent_id = ?",
                (parent_id,),
            )
        row = cursor.fetchone()
        return row["next_pos"] if row else 0

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @dataclass
    class _Tx:
        conn: sqlite3.Connection

        def __enter__(self) -> sqlite3.Connection:
            return self.conn

        def __exit__(self, exc_type, exc, tb) -> None:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()

    def _transaction(self):
        return self._Tx(self._connect())

    def _ensure_schema(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    details TEXT NOT NULL,
                    completed INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    parent_id TEXT REFERENCES tasks(task_id) ON DELETE CASCADE,
                    position INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_parent_position
                ON tasks(parent_id, position)
                """
            )
            self._maybe_migrate_from_document_store(conn)
            conn.commit()

    def _maybe_migrate_from_document_store(self, conn: sqlite3.Connection) -> None:
        if not self._has_document_table(conn):
            return
        if self._has_existing_tasks(conn):
            return
        payload = self._load_document_payload(conn)
        if payload is None:
            self._drop_document_table(conn)
            return
        tasks = self._deserialize_tasks_from_payload(payload)
        if not tasks:
            self._drop_document_table(conn)
            return
        self._insert_root_tasks(conn, tasks)
        self._drop_document_table(conn)

    def _has_document_table(self, conn: sqlite3.Connection) -> bool:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
        )
        return cursor.fetchone() is not None

    def _has_existing_tasks(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()
        return bool(row["c"])

    def _load_document_payload(self, conn: sqlite3.Connection) -> Any | None:
        row = conn.execute(
            "SELECT payload FROM documents WHERE document_key = 'tasks'"
        ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row["payload"])
        except json.JSONDecodeError:
            return None

    def _deserialize_tasks_from_payload(self, payload: Any) -> list[Task]:
        if not isinstance(payload, dict):
            return []
        payload_tasks = payload.get("tasks", [])
        if not isinstance(payload_tasks, list):
            return []
        serializer = _TaskSerializer()
        tasks: list[Task] = []
        for entry in payload_tasks:
            if isinstance(entry, dict):
                tasks.append(serializer.load(entry))
        return tasks

    def _insert_root_tasks(self, conn: sqlite3.Connection, tasks: list[Task]) -> None:
        for position, task in enumerate(tasks):
            self._insert_task(conn, task, parent_id=None, position=position)

    def _drop_document_table(self, conn: sqlite3.Connection) -> None:
        conn.execute("DROP TABLE documents")


def _attach_children(
    task_id: str,
    by_id: dict[str, Task],
    children: dict[str | None, list[str]],
) -> Task:
    task = by_id[task_id]
    ids = children.get(task_id, [])
    task.subtasks = [_attach_children(child_id, by_id, children) for child_id in ids]
    return task


def _row_to_task(row: sqlite3.Row) -> Task:
    data = {
        "task_id": row["task_id"],
        "name": row["name"],
        "details": row["details"],
        "completed": bool(row["completed"]),
        "created_at": datetime.fromisoformat(row["created_at"]),
        "updated_at": datetime.fromisoformat(row["updated_at"]),
        "subtasks": [],
    }
    return Task.model_validate(data)


def _task_to_row(task: Task, *, parent_id: str | None, position: int) -> dict[str, Any]:
    return {
        "task_id": str(task.task_id),
        "name": task.name,
        "details": task.details,
        "completed": int(task.completed),
        "created_at": _to_iso(task.created_at),
        "updated_at": _to_iso(task.updated_at),
        "parent_id": parent_id,
        "position": position,
    }


def _to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _normalise_id(task_id: str | UUID) -> str:
    return str(task_id)


@dataclass
class _TaskCollection:
    document: dict[str, Any]
    tasks: list[Task]


class _TaskSerializer:
    def load(self, payload: dict[str, Any]) -> Task:
        try:
            return Task.model_validate(payload)
        except ValidationError as exc:
            raise TaskRepositoryError(
                "Stored task payload could not be validated."
            ) from exc

    def dump(self, task: Task) -> dict[str, Any]:
        return task.model_dump(mode="json")
