from __future__ import annotations

import json
from pathlib import Path

import pytest

from tasky_shared.jsonio import atomic_write_json, read_json_document


def test_read_json_document_handles_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    result = read_json_document(path, missing_ok=True)

    assert result == {}


def test_read_json_document_raises_on_invalid(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        read_json_document(path)


def test_atomic_write_and_read_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    payload = {"name": "Tasky", "value": 42}

    atomic_write_json(path, payload)

    assert path.exists()
    assert read_json_document(path) == payload


def test_atomic_write_accepts_serialized_string(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    serialized = json.dumps({"value": "pre-serialised"})

    atomic_write_json(path, serialized)

    assert read_json_document(path) == {"value": "pre-serialised"}
