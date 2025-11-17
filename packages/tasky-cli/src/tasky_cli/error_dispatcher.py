"""Centralized error dispatcher for CLI error handling.

This module provides a registry-based error dispatcher that routes exceptions
to appropriate handlers. It consolidates error handling logic that was
previously scattered across multiple helper functions.
"""

from __future__ import annotations

import sys
import traceback
from typing import NoReturn, Protocol

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


class ErrorHandler(Protocol):
    """Protocol for exception handler functions.

    Each handler receives an exception and verbose flag, and must
    exit the process (never returns normally).
    """

    def __call__(self, exc: Exception, *, verbose: bool) -> NoReturn:
        """Handle an exception with optional verbose output.

        Args:
            exc: The exception to handle.
            verbose: If True, show detailed technical information.

        Raises:
            typer.Exit: Always raised to terminate the CLI with appropriate exit code.

        """
        ...


class ErrorDispatcher:
    """Registry-based error dispatcher for CLI exceptions.

    The dispatcher maintains a chain of (exception_type, handler) pairs
    and routes exceptions to the first matching handler. If no handler
    matches, the fallback handler is invoked.
    """

    def dispatch(self, exc: Exception, *, verbose: bool) -> NoReturn:  # noqa: C901
        """Route exception to the appropriate handler.

        Complexity is inherent to exception dispatching - we need one isinstance
        check per exception type to route to the appropriate handler. Alternative
        approaches (like a registry) introduce type safety issues.

        Args:
            exc: The exception to handle.
            verbose: If True, show detailed technical information.

        Raises:
            typer.Exit: Always raised by the handler.

        """
        # Skip typer.Exit - let it propagate
        if isinstance(exc, typer.Exit):
            raise exc

        # Route to specific handlers based on exception type
        # All handlers raise typer.Exit, so control never returns
        if isinstance(exc, TaskDomainError):
            self._handle_task_domain_error(exc, verbose=verbose)
        if isinstance(exc, StorageError):
            self._handle_storage_error(exc, verbose=verbose)
        if isinstance(exc, ProjectNotFoundError):
            self._handle_project_not_found_error(exc, verbose=verbose)
        if isinstance(exc, KeyError):
            self._handle_backend_not_registered_error(exc, verbose=verbose)
        if isinstance(exc, PydanticValidationError):
            self._handle_pydantic_validation_error(exc, verbose=verbose)

        # Fallback for unexpected errors
        self._handle_unexpected_error(exc, verbose=verbose)

    # ========== Task Domain Error Handlers ==========

    def _handle_task_domain_error(self, exc: TaskDomainError, *, verbose: bool) -> NoReturn:
        """Route task domain errors to specific handlers."""
        if isinstance(exc, TaskNotFoundError):
            self._handle_task_not_found(exc, verbose=verbose)

        if isinstance(exc, TaskValidationError):
            self._handle_task_validation_error(exc, verbose=verbose)

        if isinstance(exc, InvalidStateTransitionError):
            self._handle_invalid_transition(exc, verbose=verbose)

        # Try to handle import/export errors (will return if not applicable)
        self._try_handle_import_export_error(exc, verbose=verbose)

        # Generic task domain error
        self._render_error(str(exc) or "Task operation failed.", verbose=verbose, exc=exc)
        raise typer.Exit(1) from exc

    def _try_handle_import_export_error(self, exc: TaskDomainError, *, verbose: bool) -> None:
        """Handle import/export errors if applicable (otherwise returns)."""
        import_export_types = (
            InvalidExportFormatError,
            IncompatibleVersionError,
            ExportError,
            TaskImportError,
        )
        if not isinstance(exc, import_export_types):
            return

        if isinstance(exc, (InvalidExportFormatError, IncompatibleVersionError)):
            self._handle_import_format_error(exc, verbose=verbose)
        else:
            self._handle_import_export_error(exc, verbose=verbose)

    def _handle_task_not_found(self, exc: TaskNotFoundError, *, verbose: bool) -> NoReturn:
        """Handle TaskNotFoundError."""
        self._render_error(
            f"Task '{exc.task_id}' not found.",
            suggestion="Run 'tasky task list' to view available tasks.",
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(1) from exc

    def _handle_task_validation_error(self, exc: TaskValidationError, *, verbose: bool) -> NoReturn:
        """Handle TaskValidationError."""
        suggestion = None
        if getattr(exc, "field", None):
            suggestion = f"Check the value provided for '{exc.field}'."
        message = str(exc) or "Task validation failed."
        self._render_error(message, suggestion=suggestion, verbose=verbose, exc=exc)
        raise typer.Exit(1) from exc

    def _handle_invalid_transition(
        self,
        exc: InvalidStateTransitionError,
        *,
        verbose: bool,
    ) -> NoReturn:
        """Handle InvalidStateTransitionError."""
        # Extract user-facing labels from status values (handle both enum and string)
        from_label = getattr(exc.from_status, "value", str(exc.from_status))
        to_label = getattr(exc.to_status, "value", str(exc.to_status))

        suggestion = self._suggest_transition(
            from_status=exc.from_status,
            to_status=exc.to_status,
            task_id=str(exc.task_id),
        )
        self._render_error(
            f"Cannot transition from {from_label} to {to_label}.",
            suggestion=suggestion,
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(1) from exc

    def _handle_import_format_error(
        self,
        exc: InvalidExportFormatError | IncompatibleVersionError,
        *,
        verbose: bool,
    ) -> NoReturn:
        """Handle InvalidExportFormatError and IncompatibleVersionError."""
        if isinstance(exc, InvalidExportFormatError):
            self._render_error(
                f"Invalid file format: {exc}",
                suggestion="Ensure the file is a valid JSON export from tasky.",
                verbose=verbose,
                exc=exc,
            )
        else:  # Must be IncompatibleVersionError
            version_info = f" (found: {exc.actual})" if exc.actual else ""
            self._render_error(
                f"Incompatible format version{version_info}",
                suggestion="The export file may be from a different version of tasky.",
                verbose=verbose,
                exc=exc,
            )
        raise typer.Exit(1) from exc

    def _handle_import_export_error(
        self,
        exc: ExportError | TaskImportError,
        *,
        verbose: bool,
    ) -> NoReturn:
        """Handle ExportError and TaskImportError."""
        if isinstance(exc, ExportError):
            self._render_error(
                f"Export failed: {exc}",
                suggestion="Check file permissions and disk space.",
                verbose=verbose,
                exc=exc,
            )
        else:  # Must be TaskImportError
            self._render_error(
                f"Import failed: {exc}",
                suggestion="Verify the import file exists and is readable.",
                verbose=verbose,
                exc=exc,
            )
        raise typer.Exit(1) from exc

    # ========== Storage Error Handlers ==========

    def _handle_storage_error(self, exc: StorageError, *, verbose: bool) -> NoReturn:
        """Handle storage-related errors."""
        self._render_error(
            "Storage failure encountered. Verify project initialization and file permissions.",
            suggestion="Run 'tasky project init' or check the .tasky directory.",
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(3) from exc

    # ========== Project Error Handlers ==========

    def _handle_project_not_found_error(
        self,
        exc: ProjectNotFoundError,
        *,
        verbose: bool,
    ) -> NoReturn:
        """Handle ProjectNotFoundError."""
        self._render_error(
            "No project found in current directory.",
            suggestion="Run 'tasky project init' to create a project.",
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(1) from exc

    # ========== Backend Registry Error Handlers ==========

    def _handle_backend_not_registered_error(self, exc: KeyError, *, verbose: bool) -> NoReturn:
        """Render backend registry errors with actionable guidance."""
        details = exc.args[0] if exc.args else "Configured backend is not registered."
        self._render_error(
            str(details),
            suggestion=(
                "Update .tasky/config.toml or re-run 'tasky project init' with a valid backend."
            ),
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(1) from exc

    # ========== Validation Error Handlers ==========

    def _handle_pydantic_validation_error(
        self,
        exc: PydanticValidationError,
        *,
        verbose: bool,
    ) -> NoReturn:
        """Handle Pydantic validation errors with user-friendly messages."""
        # Extract the first error for a clean message
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = first_error.get("loc", ("unknown",))[-1]
            message = first_error.get("msg", "Validation failed")
            self._render_error(
                f"{message.capitalize()} for field '{field}'.",
                suggestion="Check your input values and try again.",
                verbose=verbose,
                exc=exc,
            )
        else:
            self._render_error(
                "Validation failed.",
                suggestion="Check your input values and try again.",
                verbose=verbose,
                exc=exc,
            )
        raise typer.Exit(1) from exc

    # ========== Fallback Handler ==========

    def _handle_unexpected_error(self, exc: Exception, *, verbose: bool) -> NoReturn:
        """Handle any unexpected errors not caught by specific handlers."""
        self._render_error(
            "An unexpected error occurred.",
            suggestion="Run with --verbose for details or file a bug report.",
            verbose=verbose,
            exc=exc,
        )
        raise typer.Exit(2) from exc

    # ========== Helper Methods ==========

    @staticmethod
    def _suggest_transition(
        from_status: TaskStatus | str,
        to_status: TaskStatus | str,
        task_id: str,
    ) -> str:
        """Generate context-aware suggestions for invalid state transitions.

        Args:
            from_status: The current status that prevents the transition.
            to_status: The desired target status.
            task_id: The task ID to include in the suggestion.

        Returns:
            A helpful suggestion string for the user.

        """
        # Normalize to TaskStatus enums for consistent comparison
        from_enum = from_status if isinstance(from_status, TaskStatus) else TaskStatus(from_status)
        to_enum = to_status if isinstance(to_status, TaskStatus) else TaskStatus(to_status)

        # Map of (from_status, to_status) -> suggestion
        reopen_suggestion = f"Use 'tasky task reopen {task_id}' to make it pending first."
        completed_suggestion = (
            f"Task is already completed. "
            f"Use 'tasky task reopen {task_id}' if you want to make changes."
        )
        cancelled_suggestion = (
            f"Task is already cancelled. "
            f"Use 'tasky task reopen {task_id}' if you want to make changes."
        )
        suggestions = {
            (TaskStatus.CANCELLED, TaskStatus.COMPLETED): reopen_suggestion,
            (TaskStatus.COMPLETED, TaskStatus.CANCELLED): reopen_suggestion,
            (TaskStatus.COMPLETED, TaskStatus.COMPLETED): completed_suggestion,
            (TaskStatus.CANCELLED, TaskStatus.CANCELLED): cancelled_suggestion,
            (TaskStatus.PENDING, TaskStatus.PENDING): "Task is already pending. No action needed.",
        }

        # Return specific suggestion or generic fallback
        return suggestions.get(
            (from_enum, to_enum),
            f"Use 'tasky task list' to inspect the current status of task '{task_id}'.",
        )

    @staticmethod
    def _render_error(
        message: str,
        *,
        suggestion: str | None = None,
        verbose: bool,
        exc: Exception | None = None,
    ) -> None:
        """Render error message with optional suggestion and traceback.

        Args:
            message: The main error message.
            suggestion: Optional suggestion for the user.
            verbose: If True, show full exception traceback.
            exc: The exception (required if verbose is True).

        """
        typer.echo(f"Error: {message}", err=True)
        if suggestion:
            typer.echo(f"Suggestion: {suggestion}", err=True)
        if verbose and exc is not None:
            typer.echo("", err=True)
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
