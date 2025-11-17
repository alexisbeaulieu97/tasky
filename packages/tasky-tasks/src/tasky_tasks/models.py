"""Models for the Tasky Tasks package."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Task state transition rules: maps each status to the set of valid target statuses
# State diagram:
#   PENDING → {COMPLETED, CANCELLED}
#   COMPLETED → {PENDING}  (reopen)
#   CANCELLED → {PENDING}  (reopen)
TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: {TaskStatus.PENDING},
    TaskStatus.CANCELLED: {TaskStatus.PENDING},
}


class TaskModel(BaseModel):
    """A model representing a task in the task management system.

    Tasks automatically track creation and modification times using UTC
    timestamps. The created_at timestamp is set once at creation, while
    updated_at is refreshed whenever mark_updated() is called.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    task_id: UUID = Field(
        default_factory=uuid4,
        description="The ID of the task.",
    )
    name: str = Field(
        ...,
        description="The name of the task.",
    )
    details: str = Field(
        ...,
        description="The details of the task.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="The status of the task.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The date and time the task was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="The date and time the task was updated.",
    )

    @field_validator("name")
    @classmethod
    def _validate_name_not_empty(cls, value: str) -> str:
        """Validate that task name is not empty or whitespace-only."""
        if not value.strip():
            msg = "Task name cannot be empty"
            raise ValueError(msg)
        return value

    @field_validator("details")
    @classmethod
    def _validate_details_not_empty(cls, value: str) -> str:
        """Validate that task details are not empty or whitespace-only."""
        if not value.strip():
            msg = "Task details cannot be empty"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _sync_initial_timestamps(self) -> TaskModel:
        """Ensure updated_at equals created_at when task is first created.

        This validator runs after model initialization and sets updated_at to
        match created_at if updated_at was not explicitly provided, ensuring
        both timestamps start with the same UTC value.
        """
        if "updated_at" not in self.model_fields_set:
            self.updated_at = self.created_at
        return self

    def mark_updated(self) -> None:
        """Refresh the updated_at timestamp to the current UTC time."""
        self.updated_at = datetime.now(tz=UTC)

    def transition_to(self, target_status: TaskStatus) -> None:
        """Transition to a new status with validation.

        This method validates that the requested transition is allowed according
        to TASK_TRANSITIONS rules, updates the status, and refreshes the
        updated_at timestamp.

        Parameters
        ----------
        target_status:
            The desired target status for this task.

        Raises
        ------
        InvalidStateTransitionError:
            Raised when the transition from the current status to the target
            status is not allowed.

        """
        # Import here to avoid circular dependency (exceptions imports TaskStatus)
        from tasky_tasks.exceptions import InvalidStateTransitionError  # noqa: PLC0415

        allowed_transitions = TASK_TRANSITIONS.get(self.status, set())
        if target_status not in allowed_transitions:
            raise InvalidStateTransitionError(
                task_id=self.task_id,
                from_status=self.status,
                to_status=target_status,
            )

        self.status = target_status
        self.mark_updated()

    def complete(self) -> None:
        """Mark this task as completed.

        Raises
        ------
        InvalidStateTransitionError:
            Raised when the task cannot be completed from its current status.

        """
        self.transition_to(TaskStatus.COMPLETED)

    def cancel(self) -> None:
        """Mark this task as cancelled.

        Raises
        ------
        InvalidStateTransitionError:
            Raised when the task cannot be cancelled from its current status.

        """
        self.transition_to(TaskStatus.CANCELLED)

    def reopen(self) -> None:
        """Reopen this task, returning it to pending status.

        Raises
        ------
        InvalidStateTransitionError:
            Raised when the task cannot be reopened from its current status.

        """
        self.transition_to(TaskStatus.PENDING)


class TaskFilter(BaseModel):
    """Filter criteria for querying tasks.

    All criteria are combined using AND logic—tasks must match all specified
    criteria to be included in results. None values indicate no filtering on
    that dimension.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    statuses: list[TaskStatus] | None = Field(
        default=None,
        description="Filter by one or more task statuses. Tasks must match at least one status.",
    )
    created_after: datetime | None = Field(
        default=None,
        description="Filter tasks created on or after this datetime (inclusive).",
    )
    created_before: datetime | None = Field(
        default=None,
        description="Filter tasks created before this datetime (exclusive).",
    )
    name_contains: str | None = Field(
        default=None,
        description="Filter tasks whose name or details contain this text (case-insensitive).",
    )

    def matches(self, task: TaskModel) -> bool:  # noqa: C901
        """Check if a task matches all filter criteria (AND logic).

        Parameters
        ----------
        task:
            The task to evaluate against filter criteria.

        Returns
        -------
        bool:
            True if the task matches all specified criteria, False otherwise.

        """
        # Status filter: task must be in one of the specified statuses
        if self.statuses is not None and task.status not in self.statuses:
            return False

        # Created after filter (inclusive)
        if self.created_after is not None and task.created_at < self.created_after:
            return False

        # Created before filter (exclusive)
        if self.created_before is not None and task.created_at >= self.created_before:
            return False

        # Text search filter (case-insensitive, searches name and details)
        if self.name_contains is not None:
            search_text = self.name_contains.lower()
            task_text = f"{task.name} {task.details}".lower()
            if search_text not in task_text:
                return False

        return True

    def matches_snapshot(self, snapshot: dict[str, object]) -> bool:  # noqa: C901
        """Check if a task snapshot matches all filter criteria (AND logic).

        This method performs filtering directly on the dictionary representation
        of a task, avoiding the expensive conversion to TaskModel. This enables
        filter-first strategies for improved performance on large datasets.

        Parameters
        ----------
        snapshot:
            The task snapshot (dict) to evaluate against filter criteria.

        Returns
        -------
        bool:
            True if the snapshot matches all specified criteria, False otherwise.

        """
        from datetime import datetime  # noqa: PLC0415

        # Status filter: task must be in one of the specified statuses
        if self.statuses is not None:
            snapshot_status = snapshot.get("status")
            # Compare against TaskStatus enum values
            status_values = [s.value for s in self.statuses]
            if snapshot_status not in status_values:
                return False

        # Date filters require parsing ISO 8601 timestamps
        created_at_str = snapshot.get("created_at")
        if created_at_str is not None and isinstance(created_at_str, str):
            try:
                # Parse ISO 8601 datetime string
                created_at = datetime.fromisoformat(created_at_str)
            except (ValueError, TypeError):
                # If parsing fails, skip this snapshot (invalid data)
                return False

            # Created after filter (inclusive)
            if self.created_after is not None and created_at < self.created_after:
                return False

            # Created before filter (exclusive)
            if self.created_before is not None and created_at >= self.created_before:
                return False

        # Text search filter (case-insensitive, searches name and details)
        if self.name_contains is not None:
            search_text = self.name_contains.lower()
            name = snapshot.get("name", "")
            details = snapshot.get("details", "")
            # Ensure name and details are strings
            if not isinstance(name, str):
                name = str(name) if name else ""
            if not isinstance(details, str):
                details = str(details) if details else ""
            task_text = f"{name} {details}".lower()
            if search_text not in task_text:
                return False

        return True
