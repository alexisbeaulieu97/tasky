"""Models for the Tasky Tasks package."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tasky_tasks.enums import TaskStatus
from tasky_tasks.exceptions import InvalidStateTransitionError

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

    def matches(self, task: TaskModel) -> bool:
        """Check whether ``task`` satisfies all configured criteria."""
        return all(
            (
                self._matches_statuses(task.status),
                self._matches_created_after(task.created_at),
                self._matches_created_before(task.created_at),
                self._matches_name_contains(task.name, task.details),
            ),
        )

    def _matches_statuses(self, status: TaskStatus) -> bool:
        """Return True when the status constraint is satisfied."""
        if self.statuses is None:
            return True
        return status in self.statuses

    def _matches_created_after(self, created_at: datetime) -> bool:
        """Return True when ``created_at`` is on/after the lower bound."""
        if self.created_after is None:
            return True
        return created_at >= self.created_after

    def _matches_created_before(self, created_at: datetime) -> bool:
        """Return True when ``created_at`` is before the upper bound."""
        if self.created_before is None:
            return True
        return created_at < self.created_before

    def _matches_name_contains(self, name: str, details: str) -> bool:
        """Return True when the text constraint matches name or details."""
        if self.name_contains is None:
            return True
        search_text = self.name_contains.lower()
        task_text = f"{name} {details}".lower()
        return search_text in task_text

    def matches_snapshot(self, snapshot: dict[str, object]) -> bool:  # noqa: C901, PLR0911
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
        # Status filter: task must be in one of the specified statuses
        if self.statuses is not None:
            snapshot_status = snapshot.get("status")
            # Compare against TaskStatus enum values
            status_values = [s.value for s in self.statuses]
            if snapshot_status not in status_values:
                return False

        # Date filters require parsing ISO 8601 timestamps
        # If any date filter is specified, reject snapshots without valid timestamps
        if self.created_after is not None or self.created_before is not None:
            created_at_str = snapshot.get("created_at")
            if not created_at_str or not isinstance(created_at_str, str):
                # Missing or invalid created_at when date filter is active
                return False

            try:
                # Parse ISO 8601 datetime string
                # Python's fromisoformat doesn't accept 'Z', so replace with +00:00
                normalized_str = created_at_str.replace("Z", "+00:00")
                created_at = datetime.fromisoformat(normalized_str)

                # Ensure timezone-aware: if naive, assume UTC
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)

            except (ValueError, TypeError):
                # If parsing fails and date filter is active, reject snapshot
                return False

            # Created after filter (inclusive) - both datetimes are now timezone-aware
            if self.created_after is not None and created_at < self.created_after:
                return False

            # Created before filter (exclusive) - both datetimes are now timezone-aware
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
