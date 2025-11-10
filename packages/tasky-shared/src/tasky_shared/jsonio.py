from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

JSON_ENCODING = "utf-8"


def read_json_document(path: Path | str, *, missing_ok: bool = False) -> Any:
    """
    Load a JSON document from disk.

    Returns an empty dict for blank or missing files when `missing_ok` is True.
    """
    file_path = Path(path)
    if missing_ok and not file_path.exists():
        return {}
    try:
        raw = file_path.read_text(encoding=JSON_ENCODING)
    except FileNotFoundError:
        if missing_ok:
            return {}
        raise
    content = raw.strip()
    if not content:
        return {}
    return json.loads(content)


def atomic_write_json(
    path: Path | str,
    payload: Mapping[str, Any] | Any,
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> Path:
    """
    Persist the provided JSON-serialisable payload atomically.

    Accepts either a mapping/list (which will be serialised) or a pre-serialised
    JSON string.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized: str
    if isinstance(payload, str):
        serialized = payload if payload.endswith("\n") else payload + "\n"
    else:
        serialized = json.dumps(payload, indent=indent, sort_keys=sort_keys) + "\n"
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding=JSON_ENCODING,
            delete=False,
            dir=target.parent,
        ) as tmp:
            tmp.write(serialized)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = Path(tmp.name)
        os.replace(temp_path, target)
        return target
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
