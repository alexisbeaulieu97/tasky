"""Tests for project configuration models."""

import json
from datetime import UTC
from pathlib import Path

import pytest
from tasky_projects import ProjectConfig, StorageConfig


def test_storage_config_defaults() -> None:
    """Test StorageConfig has correct default values."""
    config = StorageConfig()
    assert config.backend == "json"
    assert config.path == "tasks.json"


def test_storage_config_custom_values() -> None:
    """Test StorageConfig with custom values."""
    config = StorageConfig(backend="sqlite", path="db/tasks.db")
    assert config.backend == "sqlite"
    assert config.path == "db/tasks.db"


def test_project_config_defaults() -> None:
    """Test ProjectConfig has correct default values."""
    config = ProjectConfig()
    assert config.version == "1.0"
    assert config.storage.backend == "json"
    assert config.storage.path == "tasks.json"
    assert config.created_at.tzinfo is not None  # Has timezone


def test_project_config_created_at_uses_utc() -> None:
    """Test created_at timestamp uses UTC timezone."""
    config = ProjectConfig()
    assert config.created_at.tzinfo == UTC


def test_project_config_from_file_valid(tmp_path: Path) -> None:
    """Test loading valid configuration from file."""
    config_file = tmp_path / "config.json"
    config_data: dict[str, object] = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "tasks.json"},
        "created_at": "2025-11-12T10:00:00Z",
    }
    config_file.write_text(json.dumps(config_data))

    config = ProjectConfig.from_file(config_file)
    assert config.version == "1.0"
    assert config.storage.backend == "json"
    assert config.storage.path == "tasks.json"


def test_project_config_from_file_missing(tmp_path: Path) -> None:
    """Test from_file raises FileNotFoundError for missing file."""
    config_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        ProjectConfig.from_file(config_file)


def test_project_config_from_file_invalid_json(tmp_path: Path) -> None:
    """Test from_file handles invalid JSON."""
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid json}")

    with pytest.raises(json.JSONDecodeError):
        ProjectConfig.from_file(config_file)


def test_project_config_from_file_validation_error(tmp_path: Path) -> None:
    """Test from_file handles validation errors."""
    config_file = tmp_path / "config.json"
    config_data: dict[str, object] = {"version": "1.0", "storage": {"backend": 123}}  # Invalid type
    config_file.write_text(json.dumps(config_data))

    # Pydantic will raise ValidationError for invalid backend type
    with pytest.raises(Exception):  # noqa: B017, PT011
        ProjectConfig.from_file(config_file)


def test_project_config_to_file_creates_directories(tmp_path: Path) -> None:
    """Test to_file creates parent directories."""
    config_file = tmp_path / "nested" / "dir" / "config.json"
    config = ProjectConfig()

    config.to_file(config_file)

    assert config_file.exists()
    assert config_file.parent.exists()


def test_project_config_to_file_saves_data(tmp_path: Path) -> None:
    """Test to_file saves configuration data."""
    config_file = tmp_path / "config.json"
    config = ProjectConfig(
        version="1.0",
        storage=StorageConfig(backend="sqlite", path="db.sqlite"),
    )

    config.to_file(config_file)

    data = json.loads(config_file.read_text())
    assert data["version"] == "1.0"
    assert data["storage"]["backend"] == "sqlite"
    assert data["storage"]["path"] == "db.sqlite"
    assert "created_at" in data


def test_project_config_round_trip(tmp_path: Path) -> None:
    """Test saving and loading produces identical config."""
    config_file = tmp_path / "config.json"
    original = ProjectConfig(
        version="1.0",
        storage=StorageConfig(backend="json", path="tasks.json"),
    )

    # Save and reload
    original.to_file(config_file)
    loaded = ProjectConfig.from_file(config_file)

    # Compare
    assert loaded.version == original.version
    assert loaded.storage.backend == original.storage.backend
    assert loaded.storage.path == original.storage.path
    # Timestamps may have minor differences due to serialization
    assert abs((loaded.created_at - original.created_at).total_seconds()) < 1


def test_project_config_to_file_pretty_printed(tmp_path: Path) -> None:
    """Test to_file creates human-readable JSON."""
    config_file = tmp_path / "config.json"
    config = ProjectConfig()

    config.to_file(config_file)

    content = config_file.read_text()
    # Check it's pretty-printed (has newlines and indentation)
    assert "\n" in content
    assert "  " in content  # Has indentation
