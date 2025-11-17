"""Unit tests for CLI input validators."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from tasky_cli.validators import DateValidator, StatusValidator, TaskIdValidator, ValidationResult
from tasky_tasks.enums import TaskStatus


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_success_creates_valid_result(self) -> None:
        """Test that success() creates a result with is_valid=True and a value."""
        result = ValidationResult[int].success(42)

        assert result.is_valid
        assert result.value == 42
        assert result.error_message is None

    def test_failure_creates_invalid_result(self) -> None:
        """Test that failure() creates a result with is_valid=False and error message."""
        result = ValidationResult[int].failure("Something went wrong")

        assert not result.is_valid
        assert result.value is None
        assert result.error_message == "Something went wrong"

    def test_success_preserves_type(self) -> None:
        """Test that success() preserves the type of the value."""
        uuid_value = UUID("550e8400-e29b-41d4-a716-446655440000")
        result = ValidationResult[UUID].success(uuid_value)

        assert result.is_valid
        assert result.value == uuid_value
        assert isinstance(result.value, UUID)


class TestTaskIdValidator:
    """Tests for TaskIdValidator."""

    validator = TaskIdValidator()

    def test_valid_uuid_accepted(self) -> None:
        """Test that a valid UUID string is accepted and parsed."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = self.validator.validate(valid_uuid)

        assert result.is_valid
        assert result.value == UUID(valid_uuid)
        assert result.error_message is None

    def test_valid_uuid_with_whitespace_accepted(self) -> None:
        """Test that a valid UUID with leading/trailing whitespace is accepted."""
        valid_uuid = "  550e8400-e29b-41d4-a716-446655440000  "
        result = self.validator.validate(valid_uuid)

        assert result.is_valid
        assert result.value == UUID(valid_uuid.strip())

    def test_invalid_uuid_rejected(self) -> None:
        """Test that a non-UUID string is rejected with appropriate message."""
        result = self.validator.validate("abc123")

        assert not result.is_valid
        assert result.value is None
        assert result.error_message == "Invalid task ID: must be a valid UUID"

    def test_empty_string_rejected(self) -> None:
        """Test that an empty string is rejected."""
        result = self.validator.validate("")

        assert not result.is_valid
        assert result.error_message == "Invalid task ID: must be a valid UUID"

    def test_whitespace_only_rejected(self) -> None:
        """Test that whitespace-only string is rejected."""
        result = self.validator.validate("   ")

        assert not result.is_valid
        assert result.error_message == "Invalid task ID: must be a valid UUID"

    def test_partial_uuid_rejected(self) -> None:
        """Test that a partial UUID is rejected."""
        result = self.validator.validate("550e8400-e29b-41d4")

        assert not result.is_valid
        assert result.error_message == "Invalid task ID: must be a valid UUID"


class TestDateValidator:
    """Tests for DateValidator."""

    validator = DateValidator()

    def test_valid_iso_date_accepted(self) -> None:
        """Test that a valid YYYY-MM-DD date is accepted."""
        result = self.validator.validate("2025-12-31")

        assert result.is_valid
        assert result.value == datetime(2025, 12, 31, tzinfo=UTC)
        assert result.error_message is None

    def test_valid_date_with_whitespace_accepted(self) -> None:
        """Test that a valid date with leading/trailing whitespace is accepted."""
        result = self.validator.validate("  2025-12-31  ")

        assert result.is_valid
        assert result.value == datetime(2025, 12, 31, tzinfo=UTC)

    def test_invalid_format_rejected(self) -> None:
        """Test that non-ISO format is rejected."""
        result = self.validator.validate("12/31/2025")

        assert not result.is_valid
        assert result.value is None
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message
        assert "YYYY-MM-DD" in result.error_message

    def test_date_with_time_component_rejected(self) -> None:
        """Test that date strings with time components are rejected."""
        test_cases = [
            "2025-12-31T10:30:00",
            "2025-12-31 10:30:00",
            "2025-12-31T10:30:00Z",
            "2025-12-31T10:30:00+05:00",
        ]

        for date_str in test_cases:
            result = self.validator.validate(date_str)
            assert not result.is_valid, f"Should reject: {date_str}"
            assert result.error_message is not None
            assert "Invalid date format" in result.error_message

    def test_empty_string_rejected(self) -> None:
        """Test that an empty string is rejected."""
        result = self.validator.validate("")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message

    def test_whitespace_only_rejected(self) -> None:
        """Test that whitespace-only string is rejected."""
        result = self.validator.validate("   ")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message

    def test_invalid_date_values_rejected(self) -> None:
        """Test that dates with invalid values (e.g., month 13) are rejected."""
        result = self.validator.validate("2025-13-01")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message

    def test_word_format_rejected(self) -> None:
        """Test that word formats like 'tomorrow' are rejected."""
        result = self.validator.validate("tomorrow")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message

    def test_partial_date_rejected(self) -> None:
        """Test that partial dates are rejected."""
        result = self.validator.validate("2025-12")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message


class TestStatusValidator:
    """Tests for StatusValidator."""

    validator = StatusValidator()

    @pytest.mark.parametrize(
        ("status_str", "expected_status"),
        [
            ("pending", TaskStatus.PENDING),
            ("completed", TaskStatus.COMPLETED),
            ("cancelled", TaskStatus.CANCELLED),
            ("PENDING", TaskStatus.PENDING),  # Case insensitive
            ("  completed  ", TaskStatus.COMPLETED),  # Whitespace trimmed
        ],
    )
    def test_valid_status_accepted(self, status_str: str, expected_status: TaskStatus) -> None:
        """Test that valid status values are accepted."""
        result = self.validator.validate(status_str)

        assert result.is_valid
        assert result.value == expected_status
        assert result.error_message is None

    def test_invalid_status_rejected(self) -> None:
        """Test that invalid status values are rejected."""
        result = self.validator.validate("done")

        assert not result.is_valid
        assert result.value is None
        assert result.error_message is not None
        assert "Invalid status" in result.error_message
        assert "pending" in result.error_message
        assert "completed" in result.error_message
        assert "cancelled" in result.error_message

    def test_status_with_space_rejected(self) -> None:
        """Test that status with spaces (e.g., 'in progress') is rejected."""
        result = self.validator.validate("in progress")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid status" in result.error_message

    def test_empty_string_rejected(self) -> None:
        """Test that an empty string is rejected."""
        result = self.validator.validate("")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid status" in result.error_message

    def test_whitespace_only_rejected(self) -> None:
        """Test that whitespace-only string is rejected."""
        result = self.validator.validate("   ")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid status" in result.error_message

