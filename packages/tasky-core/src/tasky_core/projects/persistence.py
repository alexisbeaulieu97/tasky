from __future__ import annotations

from pathlib import Path
from typing import Any

from tasky_shared.jsonio import atomic_write_json as _atomic_write_json
from tasky_shared.jsonio import read_json_document as _read_json_document


def load_json_document(path: Path, *, missing_ok: bool = False) -> Any:
    return _read_json_document(path, missing_ok=missing_ok)


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> Path:
    return _atomic_write_json(path, payload, indent=indent, sort_keys=sort_keys)
