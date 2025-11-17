"""Input validators for Tasky CLI commands.

This module provides validators for user input that follow the project's
model-driven validation pattern. Validators wrap Pydantic model parsing and
UUID/datetime standard library functions to catch errors and return user-friendly
messages suitable for CLI display.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from tasky_tasks.enums import TaskStatus


@dataclass
class ValidationResult[T]:
    """Result of input validation, containing either a valid value or error message.

    This wrapper provides a consistent interface for all CLI validators,
    allowing commands to check validity before proceeding with service calls.

    Attributes:
        is_valid: True if validation succeeded, False otherwise.
        value: The validated and parsed value (only set if is_valid=True).
        error_message: User-friendly error description (only set if is_valid=False).

    """

    is_valid: bool
    value: T | None = None
    error_message: str | None = None

    @classmethod
    def success(cls, value: T) -> ValidationResult[T]:
        """Create a successful validation result.

        Args:
            value: The validated and parsed value.

        Returns:
            ValidationResult with is_valid=True and the value set.

        """
        return cls(is_valid=True, value=value)

    @classmethod
    def failure(cls, message: str) -> ValidationResult[T]:
        """Create a failed validation result.

        Args:
            message: User-friendly error message suitable for CLI display.

        Returns:
            ValidationResult with is_valid=False and error_message set.

        """
        return cls(is_valid=False, error_message=message)


class TaskIdValidator:
    """Validator for task ID inputs (UUID format)."""

    @staticmethod
    def validate(task_id: str) -> ValidationResult[UUID]:
        """Validate that a string is a valid UUID.

        Args:
            task_id: The task ID string provided by the user.

        Returns:
            ValidationResult containing either a parsed UUID or an error message.

        """
        if not task_id or not task_id.strip():
            return ValidationResult[UUID].failure(
                "Invalid task ID: must be a valid UUID",
            )

        try:
            parsed_uuid = UUID(task_id.strip())
            return ValidationResult[UUID].success(parsed_uuid)
        except ValueError:
            return ValidationResult[UUID].failure(
                "Invalid task ID: must be a valid UUID",
            )


class DateValidator:
    """Validator for date inputs (ISO 8601 YYYY-MM-DD format)."""

    @staticmethod
    def validate(date_str: str) -> ValidationResult[datetime]:
        """Validate that a string is in ISO 8601 date format (YYYY-MM-DD).

        Args:
            date_str: The date string provided by the user.

        Returns:
            ValidationResult containing either a parsed datetime or an error message.

        """
        if not date_str or not date_str.strip():
            return ValidationResult[datetime].failure(
                "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)",
            )

        date_str = date_str.strip()

        # Reject strings with time components
        if "T" in date_str or ":" in date_str or "+" in date_str or "Z" in date_str:
            return ValidationResult[datetime].failure(
                "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)",
            )

        # Validate format: YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return ValidationResult[datetime].failure(
                "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)",
            )

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            return ValidationResult[datetime].success(parsed_date)
        except ValueError:
            return ValidationResult[datetime].failure(
                "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)",
            )


class StatusValidator:
    """Validator for task status inputs."""

    @staticmethod
    def validate(status: str) -> ValidationResult[TaskStatus]:
        """Validate that a string is a valid task status.

        Args:
            status: The status string provided by the user.

        Returns:
            ValidationResult containing either a TaskStatus enum or an error message.

        """
        if not status or not status.strip():
            valid_statuses = ", ".join(s.value for s in TaskStatus)
            return ValidationResult[TaskStatus].failure(
                f"Invalid status. Choose from: {valid_statuses}",
            )

        status = status.strip().lower()

        try:
            # Try to match by value
            return ValidationResult[TaskStatus].success(TaskStatus(status))
        except ValueError:
            valid_statuses = ", ".join(s.value for s in TaskStatus)
            return ValidationResult[TaskStatus].failure(
                f"Invalid status. Choose from: {valid_statuses}",
            )


class PriorityValidator:
    """Validator for task priority inputs.

    Note: Currently tasky doesn't have a Priority enum, but this validator
    is provided for future use when priority support is added to TaskModel.
    """

    # Define valid priorities for now (can be replaced with enum later)
    VALID_PRIORITIES: ClassVar[set[str]] = {"low", "normal", "high"}

    @classmethod
    def validate(cls, priority: str) -> ValidationResult[str]:
        """Validate that a string is a valid task priority.

        Args:
            priority: The priority string provided by the user.

        Returns:
            ValidationResult containing either a valid priority string or an error message.

        """
        if not priority or not priority.strip():
            valid_priorities = ", ".join(sorted(cls.VALID_PRIORITIES))
            return ValidationResult[str].failure(
                f"Invalid priority. Choose from: {valid_priorities}",
            )

        priority = priority.strip().lower()

        if priority in cls.VALID_PRIORITIES:
            return ValidationResult[str].success(priority)

        valid_priorities = ", ".join(sorted(cls.VALID_PRIORITIES))
        return ValidationResult[str].failure(
            f"Invalid priority. Choose from: {valid_priorities}",
        )
