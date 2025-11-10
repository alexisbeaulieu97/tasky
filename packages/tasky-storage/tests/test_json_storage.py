import json
import tempfile
from pathlib import Path

import pytest

from tasky_storage import JsonStorage, StorageDataError


class TestJsonStorage:
    def test_initialize_creates_file_with_template(self):
        """Test that initialize creates a file with the provided template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test.json"
            store = JsonStorage(path=storage_path)

            template = {"tasks": [], "version": "1.0"}
            store.initialize(template)

            assert storage_path.exists()
            with open(storage_path, "r") as f:
                data = json.load(f)
            assert data == template

    def test_initialize_does_not_overwrite_existing_file(self):
        """Test that initialize doesn't overwrite an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test.json"
            existing_data = {"existing": "data"}

            # Create existing file
            storage_path.write_text(json.dumps(existing_data))

            store = JsonStorage(path=storage_path)
            # Try to initialize with different template
            store.initialize({"new": "template"})

            # File should still contain original data
            with open(storage_path, "r") as f:
                data = json.load(f)
            assert data == existing_data

    def test_load_reads_existing_file(self):
        """Test that load correctly reads an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test.json"
            test_data = {"tasks": [{"id": "1", "title": "Test task"}]}

            storage_path.write_text(json.dumps(test_data))

            store = JsonStorage(path=storage_path)
            loaded_data = store.load()

            assert loaded_data == test_data

    def test_save_writes_data_to_file(self):
        """Test that save correctly writes data to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test.json"
            store = JsonStorage(path=storage_path)

            test_data = {"updated": "content"}
            store.save(test_data)

            assert storage_path.exists()
            with open(storage_path, "r") as f:
                data = json.load(f)
            assert data == test_data

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading a nonexistent file raises StorageDataError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "nonexistent.json"
            store = JsonStorage(path=storage_path)

            with pytest.raises(StorageDataError):
                store.load()

    def test_save_invalid_data_raises_error(self):
        """Test that saving non-serializable data raises StorageDataError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test.json"
            store = JsonStorage(path=storage_path)

            # Try to save data with non-serializable object
            invalid_data = {"bad": set([1, 2, 3])}  # sets are not JSON serializable

            with pytest.raises(StorageDataError):
                store.save(invalid_data)
