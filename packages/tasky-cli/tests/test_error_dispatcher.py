"""Unit tests for the error dispatcher module."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import typer
from pydantic import BaseModel, ValidationError
from tasky_cli.error_dispatcher import ErrorDispatcher
from tasky_settings import ProjectNotFoundError
from tasky_storage.errors import StorageError
from tasky_tasks import (
    ExportError,
    IncompatibleVersionError,
    InvalidExportFormatError,
    InvalidStateTransitionError,
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
        """Test that typer.Exit exceptions are propagated unchanged."""
        exc = typer.Exit(code=42)
        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)
        assert exc_info.value.exit_code == 42

    def test_dispatch_task_not_found_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching TaskNotFoundError."""
        task_id = uuid4()
        exc = TaskNotFoundError(task_id=task_id)

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert f"Task '{task_id}' not found" in captured.err
        assert "tasky task list" in captured.err

    def test_dispatch_task_validation_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching TaskValidationError."""
        exc = TaskValidationError("Invalid task name")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid task name" in captured.err

    def test_dispatch_task_validation_error_with_field(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching TaskValidationError with field attribute."""
        exc = TaskValidationError("Name is required")
        exc.field = "name"  # type: ignore[attr-defined]

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Name is required" in captured.err
        assert "Check the value provided for 'name'" in captured.err

    def test_dispatch_invalid_state_transition_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching InvalidStateTransitionError."""
        task_id = uuid4()
        exc = InvalidStateTransitionError(
            task_id=task_id,
            from_status=TaskStatus.COMPLETED,
            to_status=TaskStatus.CANCELLED,
        )

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Cannot transition from completed to cancelled" in captured.err
        assert "tasky task reopen" in captured.err

    def test_dispatch_invalid_export_format_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching InvalidExportFormatError."""
        exc = InvalidExportFormatError("Not a valid JSON file")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid file format" in captured.err
        assert "valid JSON export" in captured.err

    def test_dispatch_incompatible_version_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching IncompatibleVersionError."""
        exc = IncompatibleVersionError(expected="1.0", actual="2.0")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Incompatible format version" in captured.err
        assert "found: 2.0" in captured.err

    def test_dispatch_export_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching ExportError."""
        exc = ExportError("Permission denied")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Export failed" in captured.err
        assert "Permission denied" in captured.err

    def test_dispatch_task_import_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching TaskImportError."""
        exc = TaskImportError("File not found")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Import failed" in captured.err
        assert "File not found" in captured.err

    def test_dispatch_storage_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching StorageError with exit code 3."""
        exc = StorageError("Database corruption detected")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 3
        captured = capsys.readouterr()
        assert "Storage failure encountered" in captured.err
        assert "tasky project init" in captured.err

    def test_dispatch_project_not_found_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching ProjectNotFoundError."""
        exc = ProjectNotFoundError(start_path=Path("/some/path"))

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "No project found" in captured.err
        assert "tasky project init" in captured.err

    def test_dispatch_backend_not_registered_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching KeyError (backend not registered)."""
        exc = KeyError("Backend 'sqlite' not found in registry")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr()
        assert "Backend 'sqlite' not found in registry" in captured.err
        assert "config.toml" in captured.err

    def test_dispatch_pydantic_validation_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching Pydantic ValidationError."""

        class SampleModel(BaseModel):
            name: str
            age: int

        # Trigger validation error
        try:
            SampleModel(name="John", age="invalid")  # type: ignore[arg-type]
        except ValidationError as exc:
            with pytest.raises(typer.Exit) as exc_info:
                dispatcher.dispatch(exc, verbose=False)

            assert exc_info.value.exit_code == 1
            captured = capsys.readouterr()
            assert "for field 'age'" in captured.err
            assert "Check your input values" in captured.err

    def test_dispatch_pydantic_validation_error_empty_errors(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching Pydantic ValidationError with no error details."""

        class SampleModel(BaseModel):
            name: str

        # Create a validation error and manually clear errors (edge case)
        try:
            SampleModel(name=123)  # type: ignore[arg-type]
        except ValidationError as exc:
            # Mock empty errors list
            def mock_errors() -> list[dict[str, object]]:  # type: ignore[type-arg]
                return []

            exc.errors = mock_errors  # type: ignore[method-assign]

            with pytest.raises(typer.Exit) as exc_info:
                dispatcher.dispatch(exc, verbose=False)

            assert exc_info.value.exit_code == 1
            captured = capsys.readouterr()
            assert "Validation failed" in captured.err

    def test_dispatch_unexpected_error(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test dispatching an unexpected error (fallback handler) with exit code 2."""
        exc = RuntimeError("Unexpected failure")

        with pytest.raises(typer.Exit) as exc_info:
            dispatcher.dispatch(exc, verbose=False)

        assert exc_info.value.exit_code == 2
        captured = capsys.readouterr()
        assert "An unexpected error occurred" in captured.err
        assert "Run with --verbose" in captured.err

    def test_dispatch_verbose_mode_shows_traceback(
        self,
        dispatcher: ErrorDispatcher,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that verbose mode displays full exception traceback."""
        exc = TaskNotFoundError(task_id=uuid4())

        with pytest.raises(typer.Exit):
            dispatcher.dispatch(exc, verbose=True)

        captured = capsys.readouterr()
        # Verbose mode should show exception type in traceback
        assert "TaskNotFoundError" in captured.err
        # Should have more output than non-verbose (basic test for traceback presence)
        assert len(captured.err) > 100

