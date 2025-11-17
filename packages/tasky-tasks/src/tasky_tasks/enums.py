"""Enumerations for the Tasky Tasks package."""

from __future__ import annotations

from enum import Enum


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
