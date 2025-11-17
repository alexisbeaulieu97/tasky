"""Input validators for Tasky CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ValidationError, field_validator
from tasky_tasks.enums import TaskStatus


@dataclass(slots=True)
class ValidationResult[T]:
    """Result of input validation, containing either a value or error message."""

    is_valid: bool
    value: T | None = None
    error_message: str | None = None

    @classmethod
    def success(cls, value: T) -> ValidationResult[T]:
        """Create a successful validation result."""
        return cls(is_valid=True, value=value)

    @classmethod
    def failure(cls, message: str) -> ValidationResult[T]:
        """Create a failed validation result with a user-facing message."""
        return cls(is_valid=False, error_message=message)


class Validator[T](Protocol):
    """Protocol implemented by all CLI validators."""

    def validate(self, value: str, /) -> ValidationResult[T]:
        """Validate ``value`` and return a validation result."""
        ...


class _TaskIdPayload(BaseModel):
    task_id: UUID

    @field_validator("task_id", mode="before")
    @classmethod
    def _normalize(cls, raw_value: str) -> str:
        normalized = raw_value.strip()
        if not normalized:
            msg = "Invalid task ID: must be a valid UUID"
            raise ValueError(msg)
        return normalized


class _DatePayload(BaseModel):
    date: datetime

    @field_validator("date", mode="before")
    @classmethod
    def _parse_iso_date(cls, raw_value: str) -> datetime:
        message = "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)"
        normalized = raw_value.strip()
        if not normalized:
            raise ValueError(message)

        if any(marker in normalized for marker in ("T", ":", "+", "Z")):
            raise ValueError(message)

        try:
            parsed_date = date.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(message) from exc

        return datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            tzinfo=UTC,
        )


class _StatusPayload(BaseModel):
    status: TaskStatus

    @field_validator("status", mode="before")
    @classmethod
    def _normalize(cls, raw_value: str) -> str:
        normalized = raw_value.strip().lower()
        if not normalized:
            msg = "Invalid status input"
            raise ValueError(msg)
        return normalized


class TaskIdValidator(Validator[UUID]):
    """Validator for task ID inputs (UUID format)."""

    _ERROR_MESSAGE = "Invalid task ID: must be a valid UUID"

    def validate(self, task_id: str) -> ValidationResult[UUID]:
        """Validate that ``task_id`` is a UUID."""
        try:
            payload = _TaskIdPayload.model_validate({"task_id": task_id})
        except ValidationError:
            return ValidationResult[UUID].failure(self._ERROR_MESSAGE)
        return ValidationResult[UUID].success(payload.task_id)


class DateValidator(Validator[datetime]):
    """Validator for date inputs (ISO 8601 YYYY-MM-DD format)."""

    _ERROR_MESSAGE = "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)"

    def validate(self, date_str: str) -> ValidationResult[datetime]:
        """Validate that ``date_str`` represents a YYYY-MM-DD date."""
        try:
            payload = _DatePayload.model_validate({"date": date_str})
        except ValidationError:
            return ValidationResult[datetime].failure(self._ERROR_MESSAGE)
        return ValidationResult[datetime].success(payload.date)


class StatusValidator(Validator[TaskStatus]):
    """Validator for task status inputs."""

    def validate(self, status: str) -> ValidationResult[TaskStatus]:
        """Validate CLI status input."""
        valid_statuses = ", ".join(s.value for s in TaskStatus)
        error_message = f"Invalid status. Choose from: {valid_statuses}"
        try:
            payload = _StatusPayload.model_validate({"status": status})
        except ValidationError:
            return ValidationResult[TaskStatus].failure(error_message)
        return ValidationResult[TaskStatus].success(payload.status)


task_id_validator = TaskIdValidator()
date_validator = DateValidator()
status_validator = StatusValidator()

__all__ = [
    "DateValidator",
    "StatusValidator",
    "TaskIdValidator",
    "ValidationResult",
    "Validator",
    "date_validator",
    "status_validator",
    "task_id_validator",
]
