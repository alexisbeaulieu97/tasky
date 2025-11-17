# ruff: noqa: D102
"""Unit tests for the error dispatcher module."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import typer
from pydantic import BaseModel, ValidationError
from tasky_cli.error_dispatcher import ErrorDispatcher
from tasky_hooks.errors import ErrorResult
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


@pytest.fixture
def dispatcher() -> ErrorDispatcher:
    """Create an ErrorDispatcher instance for testing."""
    return ErrorDispatcher()


class TestErrorDispatcher:
    """Test suite for ErrorDispatcher class."""

    def test_dispatch_typer_exit_propagates(self, dispatcher: ErrorDispatcher) -> None:
        exc = typer.Exit(code=42)
        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)
        assert exc_info.value.exit_code == 42

    def test_task_not_found_error(self, dispatcher: ErrorDispatcher) -> None:
        task_id = uuid4()
        exc = TaskNotFoundError(task_id=task_id)

        result = dispatcher.dispatch(exc, verbose=False)

        assert isinstance(result, ErrorResult)
        assert result.exit_code == 1
        assert f"Task '{task_id}' not found" in result.message
        assert result.suggestion == "Run 'tasky task list' to view available tasks."
        assert result.traceback is None

    def test_task_validation_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = TaskValidationError("Invalid task name")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert result.message == "Invalid task name"
        assert result.suggestion is None

    def test_task_validation_error_with_field(self, dispatcher: ErrorDispatcher) -> None:
        exc = TaskValidationError("Name is required")
        exc.field = "name"  # type: ignore[attr-defined]

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert result.message == "Name is required"
        assert result.suggestion == "Check the value provided for 'name'."

    def test_invalid_state_transition_error(self, dispatcher: ErrorDispatcher) -> None:
        task_id = uuid4()
        exc = InvalidStateTransitionError(
            task_id=task_id,
            from_status=TaskStatus.COMPLETED,
            to_status=TaskStatus.CANCELLED,
        )

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Cannot transition from completed to cancelled" in result.message
        assert "tasky task reopen" in result.suggestion

    def test_invalid_state_transition_error_with_unknown_statuses(
        self,
        dispatcher: ErrorDispatcher,
    ) -> None:
        task_id = uuid4()
        exc = InvalidStateTransitionError(
            task_id=task_id,
            from_status="UNKNOWN_STATUS",
            to_status="OTHER_STATUS",
        )

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Cannot transition from UNKNOWN_STATUS to OTHER_STATUS" in result.message
        assert "tasky task list" in result.suggestion

    def test_invalid_export_format_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = InvalidExportFormatError("Not a valid JSON file")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Invalid file format: Not a valid JSON file" in result.message
        assert "valid JSON export" in result.suggestion

    def test_incompatible_version_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = IncompatibleVersionError(expected="1.0", actual="2.0")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Incompatible format version (found: 2.0)." in result.message

    def test_export_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = ExportError("Permission denied")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Export failed: Permission denied" in result.message

    def test_import_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = TaskImportError("File not found")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Import failed: File not found" in result.message

    def test_storage_error_includes_original_message(self, dispatcher: ErrorDispatcher) -> None:
        exc = StorageError("Database corruption detected")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 3
        assert "Storage operation failed: Database corruption detected" in result.message
        assert "tasky project init" in result.suggestion

    def test_project_not_found_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = ProjectNotFoundError(start_path=Path("/some/path"))

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "No project found in current directory" in result.message
        assert "tasky project init" in result.suggestion

    def test_backend_not_registered_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = KeyError("Backend 'sqlite' not found in registry")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Backend 'sqlite' not found in registry" in result.message
        assert "config.toml" in result.suggestion

    def test_pydantic_validation_error(self, dispatcher: ErrorDispatcher) -> None:
        class SampleModel(BaseModel):
            name: str
            age: int

        with pytest.raises(ValidationError) as exc_info:
            SampleModel(name="John", age="invalid")  # type: ignore[arg-type]

        result = dispatcher.dispatch(exc_info.value, verbose=False)

        assert result.exit_code == 1
        assert "for field 'age'" in result.message
        assert "Check your input values" in result.suggestion

    def test_pydantic_validation_error_with_empty_errors(self, dispatcher: ErrorDispatcher) -> None:
        class SampleModel(BaseModel):
            name: str

        with pytest.raises(ValidationError) as exc_info:
            SampleModel(name=123)  # type: ignore[arg-type]

        validation_error = exc_info.value

        def mock_errors() -> list[dict[str, object]]:
            return []

        validation_error.errors = mock_errors  # type: ignore[method-assign]

        result = dispatcher.dispatch(validation_error, verbose=False)

        assert result.exit_code == 1
        assert "Validation failed." in result.message

    def test_generic_task_domain_error(self, dispatcher: ErrorDispatcher) -> None:
        exc = TaskDomainError("Task operation failed in service")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 1
        assert "Task operation failed in service" in result.message

    def test_unexpected_error_uses_fallback(self, dispatcher: ErrorDispatcher) -> None:
        exc = RuntimeError("Unexpected failure")

        result = dispatcher.dispatch(exc, verbose=False)

        assert result.exit_code == 2
        assert "An unexpected error occurred" in result.message
        assert "Run with --verbose" in result.suggestion

    def test_verbose_mode_includes_traceback(self, dispatcher: ErrorDispatcher) -> None:
        exc = TaskNotFoundError(task_id=uuid4())

        result = dispatcher.dispatch(exc, verbose=True)

        assert result.exit_code == 1
        assert result.traceback is not None
        assert "TaskNotFoundError" in result.traceback

    def test_custom_handler_registration(self, dispatcher: ErrorDispatcher) -> None:
        class CustomError(RuntimeError):
            pass

        def handler(
            exc: CustomError,
            *,
            verbose: bool,
        ) -> ErrorResult:  # pragma: no cover - simple stub
            message = f"custom handled ({exc})"
            suggestion = "verbose" if verbose else None
            return ErrorResult(message=message, suggestion=suggestion, exit_code=7)

        dispatcher.register(CustomError, handler)

        result = dispatcher.dispatch(CustomError(), verbose=True)

        assert result.exit_code == 7
        assert "custom handled (" in result.message
        assert result.suggestion == "verbose"
