"""Centralized error dispatcher for CLI error handling."""

from __future__ import annotations

import traceback
from typing import Protocol, TypeVar, cast

import typer
from pydantic import ValidationError as PydanticValidationError
from tasky_settings import ProjectNotFoundError
from tasky_storage.errors import StorageError
from tasky_tasks import (
    ExportError,
    IncompatibleVersionError,
    InvalidExportFormatError,
    InvalidStateTransitionError,
    TaskDomainError,
    TaskImportError,
    TaskNotFoundError,
    TaskValidationError,
)
from tasky_tasks.enums import TaskStatus

ExcT_contra = TypeVar("ExcT_contra", bound=Exception, contravariant=True)


class ErrorHandler(Protocol[ExcT_contra]):
    """Protocol for exception handler functions."""

    def __call__(self, exc: ExcT_contra, *, verbose: bool) -> str:
        """Return a formatted error message for the provided exception."""
        ...


HandlerEntry = tuple[type[Exception], ErrorHandler[Exception], int]


class ErrorDispatcher:
    """Registry-based error dispatcher for CLI exceptions."""

    def __init__(self) -> None:
        self._registry: list[HandlerEntry] = []
        self._fallback: HandlerEntry = (
            Exception,
            self._handle_unexpected_error,
            2,
        )
        self._exit_code = 1
        self._register_default_handlers()

    @property
    def exit_code(self) -> int:
        """Return the exit code produced by the most recent dispatch."""
        return self._exit_code

    def register(
        self,
        exc_type: type[ExcT_contra],
        handler: ErrorHandler[ExcT_contra],
        *,
        exit_code: int = 1,
    ) -> None:
        """Register a handler for a specific exception type."""
        entry: HandlerEntry = (exc_type, cast("ErrorHandler[Exception]", handler), exit_code)
        self._registry.append(entry)

    def dispatch(self, exc: Exception, *, verbose: bool) -> str:
        """Route exception to the first matching handler and return a message."""
        if isinstance(exc, typer.Exit):
            raise exc

        handler, exit_code = self._resolve_handler(exc)
        message = handler(exc, verbose=verbose)
        self._exit_code = exit_code
        return message

    # ========== Registry Helpers ==========

    def _register_default_handlers(self) -> None:
        """Register built-in handlers in priority order (specific → general)."""
        self.register(TaskNotFoundError, self._handle_task_not_found)
        self.register(TaskValidationError, self._handle_task_validation_error)
        self.register(InvalidStateTransitionError, self._handle_invalid_transition)
        self.register(InvalidExportFormatError, self._handle_invalid_export_format_error)
        self.register(IncompatibleVersionError, self._handle_incompatible_version_error)
        self.register(ExportError, self._handle_export_error)
        self.register(TaskImportError, self._handle_import_error)
        self.register(TaskDomainError, self._handle_generic_task_domain_error)

        self.register(StorageError, self._handle_storage_error, exit_code=1)
        self.register(ProjectNotFoundError, self._handle_project_not_found)
        self.register(KeyError, self._handle_backend_not_registered)
        self.register(PydanticValidationError, self._handle_pydantic_validation_error)

    def _resolve_handler(self, exc: Exception) -> tuple[ErrorHandler[Exception], int]:
        """Return the first registered handler that matches the exception."""
        for exc_type, handler, exit_code in self._registry:
            if isinstance(exc, exc_type):
                return handler, exit_code
        _, handler, exit_code = self._fallback
        return handler, exit_code

    # ========== Task Domain Error Handlers ==========

    def _handle_task_not_found(self, exc: TaskNotFoundError, *, verbose: bool) -> str:
        return self._format_error(
            f"Task '{exc.task_id}' not found.",
            suggestion="Run 'tasky task list' to view available tasks.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_task_validation_error(
        self,
        exc: TaskValidationError,
        *,
        verbose: bool,
    ) -> str:
        suggestion = None
        if getattr(exc, "field", None):
            suggestion = f"Check the value provided for '{exc.field}'."
        return self._format_error(
            str(exc) or "Task validation failed.",
            suggestion=suggestion,
            verbose=verbose,
            exc=exc,
        )

    def _handle_invalid_transition(
        self,
        exc: InvalidStateTransitionError,
        *,
        verbose: bool,
    ) -> str:
        from_label = getattr(exc.from_status, "value", str(exc.from_status))
        to_label = getattr(exc.to_status, "value", str(exc.to_status))
        suggestion = self._suggest_transition(
            from_status=exc.from_status,
            to_status=exc.to_status,
            task_id=str(exc.task_id),
        )
        return self._format_error(
            f"Cannot transition from {from_label} to {to_label}.",
            suggestion=suggestion,
            verbose=verbose,
            exc=exc,
        )

    def _handle_invalid_export_format_error(
        self,
        exc: InvalidExportFormatError,
        *,
        verbose: bool,
    ) -> str:
        return self._format_error(
            f"Invalid file format: {exc}",
            suggestion="Ensure the file is a valid JSON export from tasky.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_incompatible_version_error(
        self,
        exc: IncompatibleVersionError,
        *,
        verbose: bool,
    ) -> str:
        version_info = f" (found: {exc.actual})" if exc.actual else ""
        return self._format_error(
            f"Incompatible format version{version_info}.",
            suggestion="The export file may be from a different version of tasky.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_export_error(self, exc: ExportError, *, verbose: bool) -> str:
        return self._format_error(
            f"Export failed: {exc}",
            suggestion="Check file permissions and disk space.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_import_error(self, exc: TaskImportError, *, verbose: bool) -> str:
        return self._format_error(
            f"Import failed: {exc}",
            suggestion="Verify the import file exists and is readable.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_generic_task_domain_error(
        self,
        exc: TaskDomainError,
        *,
        verbose: bool,
    ) -> str:
        return self._format_error(
            str(exc) or "Task operation failed.",
            verbose=verbose,
            exc=exc,
        )

    # ========== Storage Error Handler ==========

    def _handle_storage_error(self, exc: StorageError, *, verbose: bool) -> str:
        message = f"Storage operation failed: {exc}"
        return self._format_error(
            message,
            suggestion="Run 'tasky project init' or check the .tasky directory.",
            verbose=verbose,
            exc=exc,
        )

    # ========== Project Error Handlers ==========

    def _handle_project_not_found(self, exc: ProjectNotFoundError, *, verbose: bool) -> str:
        return self._format_error(
            "No project found in current directory.",
            suggestion="Run 'tasky project init' to create a project.",
            verbose=verbose,
            exc=exc,
        )

    def _handle_backend_not_registered(self, exc: KeyError, *, verbose: bool) -> str:
        details = exc.args[0] if exc.args else "Configured backend is not registered."
        suggestion = (
            "Update .tasky/config.toml or re-run 'tasky project init' with a valid backend."
        )
        return self._format_error(
            str(details),
            suggestion=suggestion,
            verbose=verbose,
            exc=exc,
        )

    # ========== Validation Error Handler ==========

    def _handle_pydantic_validation_error(
        self,
        exc: PydanticValidationError,
        *,
        verbose: bool,
    ) -> str:
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = first_error.get("loc", ("unknown",))[-1]
            message = first_error.get("msg", "Validation failed").capitalize()
            rendered = f"{message} for field '{field}'."
        else:
            rendered = "Validation failed."
        return self._format_error(
            rendered,
            suggestion="Check your input values and try again.",
            verbose=verbose,
            exc=exc,
        )

    # ========== Fallback Handler ==========

    def _handle_unexpected_error(self, exc: Exception, *, verbose: bool) -> str:
        return self._format_error(
            "An unexpected error occurred.",
            suggestion="Run with --verbose for details or file a bug report.",
            verbose=verbose,
            exc=exc,
        )

    # ========== Helper Methods ==========

    @staticmethod
    def _suggest_transition(
        from_status: TaskStatus | str,
        to_status: TaskStatus | str,
        task_id: str,
    ) -> str:
        from_enum: TaskStatus | None
        to_enum: TaskStatus | None
        try:
            from_enum = (
                from_status
                if isinstance(from_status, TaskStatus)
                else TaskStatus(from_status)
            )
        except ValueError:
            from_enum = None
        try:
            to_enum = (
                to_status
                if isinstance(to_status, TaskStatus)
                else TaskStatus(to_status)
            )
        except ValueError:
            to_enum = None

        reopen_suggestion = f"Use 'tasky task reopen {task_id}' to make it pending first."
        completed_suggestion = (
            "Task is already completed. "
            f"Use 'tasky task reopen {task_id}' if you want to make changes."
        )
        cancelled_suggestion = (
            "Task is already cancelled. "
            f"Use 'tasky task reopen {task_id}' if you want to make changes."
        )
        suggestions = {
            (TaskStatus.CANCELLED, TaskStatus.COMPLETED): reopen_suggestion,
            (TaskStatus.COMPLETED, TaskStatus.CANCELLED): reopen_suggestion,
            (TaskStatus.COMPLETED, TaskStatus.COMPLETED): completed_suggestion,
            (TaskStatus.CANCELLED, TaskStatus.CANCELLED): cancelled_suggestion,
            (TaskStatus.PENDING, TaskStatus.PENDING): "Task is already pending. No action needed.",
        }
        if (
            from_enum is not None
            and to_enum is not None
            and (suggestion := suggestions.get((from_enum, to_enum)))
        ):
            return suggestion
        return f"Use 'tasky task list' to inspect the current status of task '{task_id}'."

    def _format_error(
        self,
        message: str,
        *,
        suggestion: str | None = None,
        verbose: bool,
        exc: Exception | None = None,
    ) -> str:
        parts = [f"Error: {message}"]
        if suggestion:
            parts.append(f"Suggestion: {suggestion}")
        if verbose and exc is not None:
            trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            parts.append("")
            parts.append(trace.rstrip())
        return "\n".join(parts)
