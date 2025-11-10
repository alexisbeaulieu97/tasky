import json
from pathlib import Path

import pytest

from tasky_settings import TaskySettings
from tasky_settings.persistence import (
    ConfigDecodeError,
    config_path,
    read_config,
    save_settings,
    write_config,
)


def test_read_config_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    assert not path.exists()

    data = read_config(tmp_path)

    assert data == {}


def test_write_config_creates_file(tmp_path: Path) -> None:
    payload = {"alpha": 1, "beta": "value"}

    written_path = write_config(payload, tmp_path)

    assert written_path == config_path(tmp_path)
    assert json.loads(written_path.read_text()) == payload


def test_save_settings_uses_tasky_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TASKY_ROOT_DIR", raising=False)
    settings = TaskySettings(tasky_dir=tmp_path)

    saved_path = save_settings(settings)

    assert saved_path == tmp_path / "config.json"
    assert json.loads(saved_path.read_text()) == {"registry_backend": "json"}


def test_read_config_raises_on_invalid_json(tmp_path: Path) -> None:
    path = config_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid", encoding="utf-8")

    with pytest.raises(ConfigDecodeError):
        read_config(tmp_path)
