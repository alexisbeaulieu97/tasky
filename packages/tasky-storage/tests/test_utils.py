"""Unit tests for shared storage utilities.

This module tests the shared utilities that are used by all storage backends
to ensure consistent serialization, deserialization, and error handling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from tasky_storage.errors import SnapshotConversionError
from tasky_storage.utils import snapshot_to_task_model, task_model_to_snapshot
from tasky_tasks.models import TaskModel, TaskStatus


class TestSnapshotToTaskModel:
    """Tests for snapshot_to_task_model utility function."""

    def test_converts_valid_snapshot_to_task_model(self) -> None:
        """Test that a valid snapshot is converted to TaskModel correctly."""
        task_id = uuid4()
        snapshot = {
            "task_id": str(task_id),
            "name": "Test Task",
            "details": "Test details",
            "status": "pending",
            "created_at": "2025-11-16T10:00:00Z",
            "updated_at": "2025-11-16T10:00:00Z",
        }

        task = snapshot_to_task_model(snapshot)

        assert task.task_id == task_id
        assert task.name == "Test Task"
        assert task.details == "Test details"
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_raises_snapshot_conversion_error_for_missing_required_field(self) -> None:
        """Test that missing required field raises SnapshotConversionError."""
        snapshot: dict[str, Any] = {
            # Missing all required fields
        }

        with pytest.raises(SnapshotConversionError) as exc_info:
            snapshot_to_task_model(snapshot)

        assert "Failed to convert snapshot" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValidationError)

    def test_raises_snapshot_conversion_error_for_invalid_uuid(self) -> None:
        """Test that invalid UUID format raises SnapshotConversionError."""
        snapshot = {
            "task_id": "not-a-valid-uuid",
            "name": "Test Task",
            "details": "Test details",
            "status": "pending",
            "created_at": "2025-11-16T10:00:00Z",
            "updated_at": "2025-11-16T10:00:00Z",
        }

        with pytest.raises(SnapshotConversionError) as exc_info:
            snapshot_to_task_model(snapshot)

        assert "Failed to convert snapshot" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None

    def test_raises_snapshot_conversion_error_for_invalid_enum_value(self) -> None:
        """Test that invalid enum value raises SnapshotConversionError."""
        snapshot = {
            "task_id": str(uuid4()),
            "name": "Test Task",
            "details": "Test details",
            "status": "invalid_status",
            "created_at": "2025-11-16T10:00:00Z",
            "updated_at": "2025-11-16T10:00:00Z",
        }

        with pytest.raises(SnapshotConversionError) as exc_info:
            snapshot_to_task_model(snapshot)

        assert "Failed to convert snapshot" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None

    def test_raises_snapshot_conversion_error_for_malformed_datetime(self) -> None:
        """Test that malformed datetime string raises SnapshotConversionError."""
        snapshot = {
            "task_id": str(uuid4()),
            "name": "Test Task",
            "details": "Test details",
            "status": "pending",
            "created_at": "not-a-datetime",
            "updated_at": "2025-11-16T10:00:00Z",
        }

        with pytest.raises(SnapshotConversionError) as exc_info:
            snapshot_to_task_model(snapshot)

        assert "Failed to convert snapshot" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None

    def test_preserves_original_validation_error_in_cause(self) -> None:
        """Test that original ValidationError is preserved in __cause__."""
        snapshot = {"name": "Missing required fields"}

        with pytest.raises(SnapshotConversionError) as exc_info:
            snapshot_to_task_model(snapshot)

        assert isinstance(exc_info.value.__cause__, ValidationError)
        # Verify we can still access the original Pydantic error details
        assert len(exc_info.value.__cause__.errors()) > 0

    def test_handles_all_task_statuses(self) -> None:
        """Test that all valid task statuses are handled correctly."""
        for status in ["pending", "completed", "cancelled"]:
            snapshot = {
                "task_id": str(uuid4()),
                "name": "Test Task",
                "details": "Test details",
                "status": status,
                "created_at": "2025-11-16T10:00:00Z",
                "updated_at": "2025-11-16T10:00:00Z",
            }

            task = snapshot_to_task_model(snapshot)
            assert task.status.value == status


class TestTaskModelToSnapshot:
    """Tests for task_model_to_snapshot utility function."""

    def test_serializes_task_to_snapshot_with_json_mode(self) -> None:
        """Test that TaskModel is serialized correctly with mode='json'."""
        task = TaskModel(name="Test Task", details="Test details")

        snapshot = task_model_to_snapshot(task)

        assert isinstance(snapshot, dict)
        assert "task_id" in snapshot
        assert "name" in snapshot
        assert "details" in snapshot
        assert "status" in snapshot
        assert "created_at" in snapshot
        assert "updated_at" in snapshot

    def test_serializes_datetime_as_iso_string(self) -> None:
        """Test that datetime fields are serialized as ISO 8601 strings."""
        task = TaskModel(name="Test Task", details="Test details")

        snapshot = task_model_to_snapshot(task)

        assert isinstance(snapshot["created_at"], str)
        assert isinstance(snapshot["updated_at"], str)
        # Verify ISO 8601 format with timezone
        assert "T" in snapshot["created_at"]
        assert snapshot["created_at"].endswith("Z")

    def test_serializes_enum_as_string(self) -> None:
        """Test that enum fields are serialized as string values."""
        task = TaskModel(name="Test Task", details="Test details")

        snapshot = task_model_to_snapshot(task)

        assert isinstance(snapshot["status"], str)
        assert snapshot["status"] == "pending"

    def test_serializes_uuid_as_string(self) -> None:
        """Test that UUID fields are serialized as strings."""
        task = TaskModel(name="Test Task", details="Test details")

        snapshot = task_model_to_snapshot(task)

        assert isinstance(snapshot["task_id"], str)
        # Verify it's a valid UUID string format
        assert len(snapshot["task_id"]) == 36
        assert snapshot["task_id"].count("-") == 4

    def test_roundtrip_serialization_preserves_data(self) -> None:
        """Test that serialization roundtrip produces identical TaskModel."""
        original_task = TaskModel(name="Test Task", details="Test details")

        # Serialize and deserialize
        snapshot = task_model_to_snapshot(original_task)
        restored_task = snapshot_to_task_model(snapshot)

        # Verify all fields match
        assert restored_task.task_id == original_task.task_id
        assert restored_task.name == original_task.name
        assert restored_task.details == original_task.details
        assert restored_task.status == original_task.status
        assert restored_task.created_at == original_task.created_at
        assert restored_task.updated_at == original_task.updated_at

    def test_roundtrip_with_all_statuses(self) -> None:
        """Test roundtrip serialization with all task statuses."""
        for status in [TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            task = TaskModel(name="Test Task", details="Test details")
            if status == TaskStatus.COMPLETED:
                task.complete()
            elif status == TaskStatus.CANCELLED:
                task.cancel()

            snapshot = task_model_to_snapshot(task)
            restored_task = snapshot_to_task_model(snapshot)

            assert restored_task.status == status

    def test_json_serialization_roundtrip(self) -> None:
        """Test that snapshot can be serialized to JSON and back."""
        import json  # noqa: PLC0415

        task = TaskModel(name="Test Task", details="Test details")

        # Serialize to snapshot, then to JSON string
        snapshot = task_model_to_snapshot(task)
        json_string = json.dumps(snapshot)

        # Parse JSON and deserialize back to TaskModel
        parsed_snapshot = json.loads(json_string)
        restored_task = snapshot_to_task_model(parsed_snapshot)

        # Verify task is identical
        assert restored_task.task_id == task.task_id
        assert restored_task.name == task.name
        assert restored_task.details == task.details
        assert restored_task.status == task.status

    def test_snapshot_keys_are_deterministic(self) -> None:
        """Test that snapshot keys are in a consistent order."""
        task1 = TaskModel(name="Task 1", details="Details 1")
        task2 = TaskModel(name="Task 2", details="Details 2")

        snapshot1 = task_model_to_snapshot(task1)
        snapshot2 = task_model_to_snapshot(task2)

        # Keys should be in the same order
        assert list(snapshot1.keys()) == list(snapshot2.keys())

    def test_handles_minimal_details(self) -> None:
        """Test that minimal details field is handled correctly."""
        task = TaskModel(name="Test Task", details=".")

        snapshot = task_model_to_snapshot(task)
        restored_task = snapshot_to_task_model(snapshot)

        assert restored_task.details == "."

    def test_handles_long_strings(self) -> None:
        """Test that very long strings are handled correctly."""
        long_name = "A" * 1000
        long_details = "B" * 10000

        task = TaskModel(name=long_name, details=long_details)

        snapshot = task_model_to_snapshot(task)
        restored_task = snapshot_to_task_model(snapshot)

        assert restored_task.name == long_name
        assert restored_task.details == long_details

    def test_handles_special_characters(self) -> None:
        """Test that special characters are handled correctly."""
        task = TaskModel(
            name='Test "quotes" and \\backslashes\\',
            details="Unicode: 你好世界 🌍",
        )

        snapshot = task_model_to_snapshot(task)
        restored_task = snapshot_to_task_model(snapshot)

        assert restored_task.name == task.name
        assert restored_task.details == task.details


class TestCrossBackendConsistency:
    """Tests to verify snapshot format is consistent across backends."""

    def test_same_task_produces_identical_snapshot(self) -> None:
        """Test that the same task always produces identical snapshot."""
        task_id = uuid4()
        created_at = datetime.now(UTC)
        updated_at = created_at

        # Create task with fixed values
        task1 = TaskModel(
            task_id=task_id,
            name="Test Task",
            details="Test details",
            created_at=created_at,
            updated_at=updated_at,
        )

        task2 = TaskModel(
            task_id=task_id,
            name="Test Task",
            details="Test details",
            created_at=created_at,
            updated_at=updated_at,
        )

        snapshot1 = task_model_to_snapshot(task1)
        snapshot2 = task_model_to_snapshot(task2)

        # Snapshots should be identical
        assert snapshot1 == snapshot2

    def test_snapshot_format_matches_spec(self) -> None:
        """Test that snapshot format matches OpenSpec requirements."""
        task = TaskModel(name="Test Task", details="Test details")

        snapshot = task_model_to_snapshot(task)

        # Verify ISO 8601 datetime format with timezone
        assert isinstance(snapshot["created_at"], str)
        assert "T" in snapshot["created_at"]
        assert snapshot["created_at"].endswith("Z")

        # Verify enum as string
        assert isinstance(snapshot["status"], str)
        assert snapshot["status"] in ["pending", "completed", "cancelled"]

        # Verify UUID as string
        assert isinstance(snapshot["task_id"], str)

        # Verify all required fields present
        required_fields = {"task_id", "name", "details", "status", "created_at", "updated_at"}
        assert set(snapshot.keys()) == required_fields
