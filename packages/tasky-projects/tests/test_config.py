"""Tests for project configuration models."""

import json
import os
import stat
import sys
import tomllib
from datetime import UTC
from pathlib import Path

import pytest
import tomli_w
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
    """Test loading valid configuration from TOML file."""
    config_file = tmp_path / "config.toml"
    config_data: dict[str, object] = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "tasks.json"},
        "created_at": "2025-11-12T10:00:00Z",
    }
    with config_file.open("wb") as f:
        tomli_w.dump(config_data, f)

    config = ProjectConfig.from_file(config_file)
    assert config.version == "1.0"
    assert config.storage.backend == "json"
    assert config.storage.path == "tasks.json"


def test_project_config_from_file_missing(tmp_path: Path) -> None:
    """Test from_file raises FileNotFoundError for missing file."""
    config_file = tmp_path / "nonexistent.toml"

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        ProjectConfig.from_file(config_file)


def test_project_config_from_file_invalid_toml(tmp_path: Path) -> None:
    """Test from_file handles invalid TOML."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("{invalid toml}")

    with pytest.raises(tomllib.TOMLDecodeError):
        ProjectConfig.from_file(config_file)


def test_project_config_from_file_validation_error(tmp_path: Path) -> None:
    """Test from_file handles validation errors."""
    config_file = tmp_path / "config.toml"
    config_data: dict[str, object] = {"version": "1.0", "storage": {"backend": 123}}  # Invalid type
    with config_file.open("wb") as f:
        tomli_w.dump(config_data, f)

    # Pydantic will raise ValidationError for invalid backend type
    with pytest.raises(Exception):  # noqa: B017, PT011
        ProjectConfig.from_file(config_file)


def test_project_config_to_file_creates_directories(tmp_path: Path) -> None:
    """Test to_file creates parent directories."""
    config_file = tmp_path / "nested" / "dir" / "config.toml"
    config = ProjectConfig()

    config.to_file(config_file)

    assert config_file.exists()
    assert config_file.parent.exists()


def test_project_config_to_file_saves_data(tmp_path: Path) -> None:
    """Test to_file saves configuration data in TOML format."""
    config_file = tmp_path / "config.toml"
    config = ProjectConfig(
        version="1.0",
        storage=StorageConfig(backend="sqlite", path="db.sqlite"),
    )

    config.to_file(config_file)

    with config_file.open("rb") as f:
        data = tomllib.load(f)
    assert data["version"] == "1.0"
    assert data["storage"]["backend"] == "sqlite"
    assert data["storage"]["path"] == "db.sqlite"
    assert "created_at" in data


def test_project_config_round_trip(tmp_path: Path) -> None:
    """Test saving and loading produces identical config."""
    config_file = tmp_path / "config.toml"
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


def test_project_config_to_file_creates_toml(tmp_path: Path) -> None:
    """Test to_file creates valid TOML file."""
    config_file = tmp_path / "config.toml"
    config = ProjectConfig()

    config.to_file(config_file)

    # Verify it's valid TOML by parsing it
    with config_file.open("rb") as f:
        data = tomllib.load(f)
    assert "version" in data
    assert "storage" in data


# Legacy JSON Migration Tests


def test_project_config_from_file_legacy_json(tmp_path: Path) -> None:
    """Test loading legacy JSON configuration with migration warning."""
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


def test_project_config_auto_detects_toml(tmp_path: Path) -> None:
    """Test auto-detection prefers TOML over JSON."""
    # Create both files
    json_file = tmp_path / "config.json"
    toml_file = tmp_path / "config.toml"

    json_data = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "tasks.json"},
        "created_at": "2025-11-12T10:00:00Z",
    }
    toml_data = {
        "version": "2.0",
        "storage": {"backend": "sqlite", "path": "db.sqlite"},
        "created_at": "2025-11-12T11:00:00Z",
    }

    json_file.write_text(json.dumps(json_data))
    with toml_file.open("wb") as f:
        tomli_w.dump(toml_data, f)

    # When both exist, TOML should be preferred
    config = ProjectConfig.from_file(tmp_path / "config.toml")
    assert config.version == "2.0"
    assert config.storage.backend == "sqlite"


def test_project_config_auto_detects_with_nonexistent_path(tmp_path: Path) -> None:
    """Test auto-detection works when provided path doesn't exist."""
    # Create config.toml but call from_file with a different (non-existent) path
    toml_file = tmp_path / "config.toml"
    toml_data = {
        "version": "1.5",
        "storage": {"backend": "sqlite", "path": "db.sqlite"},
        "created_at": "2025-11-12T11:00:00Z",
    }
    with toml_file.open("wb") as f:
        tomli_w.dump(toml_data, f)

    # Call with a non-existent path - should auto-detect config.toml
    nonexistent = tmp_path / "nonexistent.toml"
    config = ProjectConfig.from_file(nonexistent)
    assert config.version == "1.5"


def test_project_config_auto_detects_legacy_json_with_nonexistent_path(
    tmp_path: Path,
) -> None:
    """Test auto-detection finds legacy JSON when TOML doesn't exist."""
    # Create only config.json
    json_file = tmp_path / "config.json"
    json_data = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "tasks.json"},
        "created_at": "2025-11-12T10:00:00Z",
    }
    json_file.write_text(json.dumps(json_data))

    # Call with a non-existent path - should auto-detect config.json
    nonexistent = tmp_path / "nonexistent.toml"
    config = ProjectConfig.from_file(nonexistent)
    assert config.version == "1.0"
    assert config.storage.backend == "json"


def test_project_config_json_to_toml_migration(tmp_path: Path) -> None:
    """Test migrating from JSON to TOML on write."""
    json_file = tmp_path / "config.json"
    toml_file = tmp_path / "config.toml"

    # Create legacy JSON config
    config_data = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "tasks.json"},
        "created_at": "2025-11-12T10:00:00Z",
    }
    json_file.write_text(json.dumps(config_data))

    # Load from JSON
    config = ProjectConfig.from_file(json_file)

    # Save (should create TOML)
    config.to_file(toml_file)

    # Verify TOML was created
    assert toml_file.exists()
    with toml_file.open("rb") as f:
        loaded = tomllib.load(f)
    assert loaded["version"] == "1.0"


def test_project_config_to_file_forces_toml_extension(tmp_path: Path) -> None:
    """Test to_file always creates .toml file even if .json path provided."""
    json_path = tmp_path / "config.json"
    config = ProjectConfig()

    config.to_file(json_path)

    # Should create config.toml, not config.json
    toml_path = tmp_path / "config.toml"
    assert toml_path.exists()
    assert not json_path.exists()


def test_project_config_to_file_sets_secure_permissions(tmp_path: Path) -> None:
    """Test to_file sets file permissions to 0o600 on POSIX systems."""
    config_file = tmp_path / "config.toml"
    config = ProjectConfig()

    config.to_file(config_file)

    # Only check permissions on POSIX systems (Linux, macOS, etc.)
    if os.name == "posix" and sys.platform != "win32":
        file_stat = config_file.stat()
        # Get permission bits (last 3 octal digits)
        permissions = stat.S_IMODE(file_stat.st_mode)
        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"
