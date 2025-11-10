from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from tasky_storage import JsonDocumentStore, SQLiteDocumentStore, StorageDataError


def test_load_returns_empty_dict_when_file_missing(tmp_path: Path) -> None:
    store = JsonDocumentStore(tmp_path / "data.json")

    assert store.load() == {}


def test_save_writes_document(tmp_path: Path) -> None:
    store = JsonDocumentStore(tmp_path / "data.json")

    store.save({"tasks": [{"id": "task-1"}]})

    persisted = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert persisted == {"tasks": [{"id": "task-1"}]}


def test_load_reads_previous_document(tmp_path: Path) -> None:
    storage_path = tmp_path / "data.json"
    storage_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")
    store = JsonDocumentStore(storage_path)

    assert store.load() == {"tasks": []}


def test_load_raises_for_non_object_payload(tmp_path: Path) -> None:
    storage_path = tmp_path / "data.json"
    storage_path.write_text("[]", encoding="utf-8")
    store = JsonDocumentStore(storage_path)

    with pytest.raises(StorageDataError):
        store.load()


def test_load_raises_for_corrupt_json(tmp_path: Path) -> None:
    storage_path = tmp_path / "data.json"
    storage_path.write_text("not-json", encoding="utf-8")
    store = JsonDocumentStore(storage_path)

    with pytest.raises(StorageDataError):
        store.load()


def test_save_raises_for_non_serialisable_types(tmp_path: Path) -> None:
    store = JsonDocumentStore(tmp_path / "data.json")

    with pytest.raises(StorageDataError):
        store.save({"bad": set()})  # type: ignore[arg-type]


class StubSerializer:
    def __init__(self) -> None:
        self.loads_payload: str | None = None
        self.dumps_document: Mapping[str, Any] | None = None

    def loads(self, payload: str) -> dict[str, Any]:
        self.loads_payload = payload
        return {"loaded": True}

    def dumps(self, document: Mapping[str, Any]) -> str:
        self.dumps_document = document
        return "serialized"


class StubGateway:
    def __init__(self, path: Path, initial: str | None = None) -> None:
        self._path = path
        self.read_value = initial
        self.written: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> str | None:
        return self.read_value

    def write(self, content: str) -> None:
        self.written = content


def test_json_store_accepts_custom_serializer_and_gateway(tmp_path: Path) -> None:
    storage_path = tmp_path / "custom.json"
    serializer = StubSerializer()
    gateway = StubGateway(storage_path, initial='{"foo": "bar"}')
    store = JsonDocumentStore(
        storage_path,
        serializer=serializer,
        gateway=gateway,
    )

    loaded = store.load()
    store.save({"baz": 1})

    assert loaded == {"loaded": True}
    assert serializer.loads_payload == '{"foo": "bar"}'
    assert serializer.dumps_document == {"baz": 1}
    assert gateway.written == "serialized"


def test_sqlite_document_store_round_trip(tmp_path: Path) -> None:
    store = SQLiteDocumentStore(tmp_path / "tasks.sqlite")

    assert store.load() == {}
    store.save({"tasks": [{"name": "demo"}]})
    assert store.load() == {"tasks": [{"name": "demo"}]}
