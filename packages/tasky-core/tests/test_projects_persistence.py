from __future__ import annotations

import json
from pathlib import Path

import pytest

from tasky_core.projects.persistence import atomic_write_json, load_json_document


def test_load_json_document_returns_empty_for_missing_file(tmp_path: Path) -> None:
    target = tmp_path / "missing.json"

    data = load_json_document(target, missing_ok=True)

    assert data == {}


def test_load_json_document_raises_when_missing_and_not_allowed(tmp_path: Path) -> None:
    target = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_json_document(target)


def test_atomic_write_json_overwrites_content_atomically(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text('{"old": true}\n', encoding="utf-8")

    atomic_write_json(target, {"new": 1})

    payload = target.read_text(encoding="utf-8")
    assert payload.endswith("\n")
    assert json.loads(payload) == {"new": 1}
