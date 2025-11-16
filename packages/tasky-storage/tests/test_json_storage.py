"""Tests for the JsonStorage class in tasky-storage package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tasky_storage import JsonStorage, StorageDataError, StorageIOError


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def storage_path(temp_dir: Path) -> Path:
    """Provide a storage path in the temp directory."""
    return temp_dir / "test.json"


@pytest.fixture
def store(storage_path: Path) -> JsonStorage:
    """Provide a JsonStorage instance."""
    return JsonStorage(path=storage_path)


class TestJsonStorage:
    """Tests for the JsonStorage class."""

    @staticmethod
    def _read_json_file(path: Path) -> dict[str, Any]:
        """Read and parse JSON file."""
        with path.open() as f:
            return json.load(f)

    def test_initialize_creates_file_with_template(
        self,
        storage_path: Path,
        store: JsonStorage,
    ) -> None:
        """Test that initialize creates a file with the provided template."""
        template: dict[str, Any] = {"tasks": [], "version": "1.0"}
        store.initialize(template)

        assert storage_path.exists()
        assert self._read_json_file(storage_path) == template

    def test_initialize_does_not_overwrite_existing_file(
        self,
        storage_path: Path,
        store: JsonStorage,
    ) -> None:
        """Test that initialize doesn't overwrite an existing file."""
        existing_data = {"existing": "data"}
        storage_path.write_text(json.dumps(existing_data))

        store.initialize({"new": "template"})

        assert self._read_json_file(storage_path) == existing_data

    def test_load_reads_existing_file(self, storage_path: Path, store: JsonStorage) -> None:
        """Test that load correctly reads an existing file."""
        test_data = {"tasks": [{"id": "1", "title": "Test task"}]}
        storage_path.write_text(json.dumps(test_data))

        loaded_data = store.load()

        assert loaded_data == test_data

    def test_save_writes_data_to_file(self, storage_path: Path, store: JsonStorage) -> None:
        """Test that save correctly writes data to file."""
        test_data = {"updated": "content"}

        store.save(test_data)

        assert storage_path.exists()
        assert self._read_json_file(storage_path) == test_data

    def test_load_nonexistent_file_raises_error(self, temp_dir: Path) -> None:
        """Test that loading a nonexistent file raises StorageIOError."""
        storage_path = temp_dir / "nonexistent.json"
        store = JsonStorage(path=storage_path)

        with pytest.raises(StorageIOError):
            store.load()

    def test_save_invalid_data_raises_error(self, store: JsonStorage) -> None:
        """Test that saving non-serializable data raises StorageDataError."""
        invalid_data = {"bad": {1, 2, 3}}  # sets are not JSON serializable

        with pytest.raises(StorageDataError):
            store.save(invalid_data)
