"""Domain exception hierarchy for task management operations."""

from __future__ import annotations

from uuid import UUID

from tasky_tasks.enums import TaskStatus


class TaskDomainError(Exception):
    """Base exception for all task-related domain violations.

    Parameters
    ----------
    message:
        Human-readable description of the failure. When omitted, subclasses
        provide an appropriate default message.
    **context:
        Arbitrary keyword arguments containing structured context for the
        failure (for example, ``task_id`` or ``from_status``).

    """

    def __init__(self, message: str | None = None, **context: object) -> None:
        self.message = message or "Task domain error."
        self.context = dict(context)
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return the human-readable message for end users."""
        return self.message

    def __repr__(self) -> str:
        """Return a detailed representation including structured context."""
        context_parts = ", ".join(f"{key}={value!r}" for key, value in self.context.items())
        if context_parts:
            return f"{self.__class__.__name__}(message={self.message!r}, {context_parts})"
        return f"{self.__class__.__name__}(message={self.message!r})"


class TaskNotFoundError(TaskDomainError):
    """Raised when an operation references a task that does not exist."""

    def __init__(self, task_id: UUID | str, message: str | None = None) -> None:
        self.task_id = task_id
        default_message = message or f"Task '{task_id}' was not found."
        super().__init__(default_message, task_id=str(task_id))


class TaskValidationError(TaskDomainError):
    """Raised when task data fails validation rules."""

    def __init__(self, message: str | None = None, *, field: str | None = None) -> None:
        self.field = field
        default_message = message or "Task validation failed."
        context: dict[str, object] = {}
        if field is not None:
            context["field"] = field
        super().__init__(default_message, **context)


class InvalidStateTransitionError(TaskDomainError):
    """Raised when attempting an invalid status transition for a task."""

    def __init__(
        self,
        task_id: UUID | str,
        from_status: TaskStatus | str,
        to_status: TaskStatus | str,
        message: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.from_status = from_status
        self.to_status = to_status
        from_label = self._as_status_label(from_status)
        to_label = self._as_status_label(to_status)
        default_message = message or (
            f"Cannot transition task '{task_id}' from {from_label} to {to_label}."
        )
        super().__init__(
            default_message,
            task_id=str(task_id),
            from_status=from_label,
            to_status=to_label,
        )

    @staticmethod
    def _as_status_label(status: TaskStatus | str) -> str:
        return status.value if isinstance(status, TaskStatus) else str(status)


class ImportExportError(TaskDomainError):
    """Base exception for import/export operations."""

    def __init__(self, message: str | None = None) -> None:
        default_message = message or "Import/export operation failed."
        super().__init__(default_message)


class ExportError(ImportExportError):
    """Raised when task export fails."""

    def __init__(self, message: str | None = None) -> None:
        default_message = message or "Task export failed."
        super().__init__(default_message)


class TaskImportError(ImportExportError):
    """Raised when task import fails."""

    def __init__(self, message: str | None = None) -> None:
        default_message = message or "Task import failed."
        super().__init__(default_message)


class InvalidExportFormatError(ImportExportError):
    """Raised when export file format is invalid or malformed."""

    def __init__(self, message: str | None = None) -> None:
        default_message = message or "Invalid export file format."
        super().__init__(default_message)


class IncompatibleVersionError(ImportExportError):
    """Raised when export format version is incompatible."""

    def __init__(
        self,
        message: str | None = None,
        *,
        expected: str | None = None,
        actual: str | None = None,
    ) -> None:
        self.expected = expected
        self.actual = actual
        default_message = message or "Incompatible export format version."
        context: dict[str, object] = {}
        if expected is not None:
            context["expected"] = expected
        if actual is not None:
            context["actual"] = actual
        super().__init__(default_message)
        self.context.update(context)
