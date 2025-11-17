"""Tests for CLI error handling and presentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from tasky_cli import app
from tasky_cli.commands import tasks as tasks_module
from tasky_storage.errors import StorageConfigurationError, StorageError
from tasky_tasks import (
    InvalidStateTransitionError,
    TaskNotFoundError,
    TaskValidationError,
)
from tasky_tasks.enums import TaskStatus
from typer.testing import CliRunner

if TYPE_CHECKING:
    from tasky_tasks.models import TaskModel

runner = CliRunner()


class _TaskServiceStub:
    """Task service stub that raises a configured exception."""

    def __init__(
        self,
        error: Exception | None = None,
        tasks: list[TaskModel] | None = None,
    ) -> None:
        self._error = error
        self._tasks = tasks or []

    def get_all_tasks(self) -> list[TaskModel]:
        if self._error is not None:
            raise self._error
        return self._tasks


def _prepare_workspace() -> None:
    storage_root = Path(".tasky")
    storage_root.mkdir(exist_ok=True)
    (storage_root / "tasks.json").write_text("{}")


def test_task_not_found_error_is_presented_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI should format TaskNotFoundError with friendly message."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            return _TaskServiceStub(TaskNotFoundError("abc"))

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "Error: Task 'abc' not found." in result.stderr
        assert "Suggestion: Run 'tasky task list' to view available tasks." in result.stderr
        assert "Traceback" not in result.stderr


def test_storage_error_results_in_exit_code_three(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI should map storage failures to exit code 3."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            return _TaskServiceStub(StorageConfigurationError("boom"))

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 3
        assert "Storage failure encountered." in result.stderr


def test_invalid_storage_data_triggers_error_without_patch() -> None:
    """Invalid storage documents should surface as storage failures."""
    with runner.isolated_filesystem():
        # First initialize project
        runner.invoke(app, ["project", "init"])

        # Then corrupt the tasks file
        storage_root = Path(".tasky")
        invalid_document: dict[str, object] = {
            "version": "1.0",
            "tasks": {
                "bad": {
                    "task_id": "not-a-uuid",
                    "name": "Corrupted task",
                    "details": "Corrupted details",
                },
            },
        }
        (storage_root / "tasks.json").write_text(json.dumps(invalid_document))

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 3
        assert "Storage failure encountered." in result.stderr


def test_verbose_mode_outputs_stack_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verbose flag should show stack trace for domain errors."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            return _TaskServiceStub(TaskNotFoundError("xyz"))

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "--verbose", "list"])

        assert result.exit_code == 1
        assert "Traceback (most recent call last)" in result.stderr


# ============================================================================
# Section 1: Error Handler Path Testing
# ============================================================================


def test_handle_task_validation_error_with_friendly_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should format TaskValidationError with friendly message."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            error = TaskValidationError("Invalid priority value")
            return _TaskServiceStub(error)

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "Invalid priority value" in result.stderr
        assert "Traceback" not in result.stderr


def test_handle_invalid_state_transition_with_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should format InvalidStateTransitionError with actionable suggestion."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            from uuid import uuid4  # noqa: PLC0415

            task_id = uuid4()
            error = InvalidStateTransitionError(
                task_id=task_id,
                from_status=TaskStatus.COMPLETED,
                to_status=TaskStatus.PENDING,
            )
            return _TaskServiceStub(error)

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "Cannot transition from completed to pending" in result.stderr
        assert "Traceback" not in result.stderr


def test_handle_storage_error_with_correct_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should map StorageError to exit code 3."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            error = StorageError("Disk write failed")
            return _TaskServiceStub(error)

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 3
        assert "Storage failure encountered" in result.stderr


def test_handle_project_not_found_with_init_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should suggest running 'project init' when project not found."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            from pathlib import Path  # noqa: PLC0415

            from tasky_settings import (  # noqa: PLC0415
                ProjectNotFoundError as SettingsProjectNotFoundError,
            )

            error = SettingsProjectNotFoundError(Path.cwd())
            return _TaskServiceStub(error)

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "No project found" in result.stderr
        assert "tasky project init" in result.stderr


def test_handle_generic_error_shows_bug_report_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should suggest filing bug report for unexpected errors."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            error = RuntimeError("Unexpected internal error")
            return _TaskServiceStub(error)

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 2  # Exit code 2 for unexpected/internal errors
        assert "unexpected error occurred" in result.stderr.lower()
        assert "--verbose" in result.stderr or "bug report" in result.stderr.lower()


def test_error_messages_have_no_python_stack_traces_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should not show Python stack traces without --verbose flag."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        def _factory() -> _TaskServiceStub:
            return _TaskServiceStub(TaskNotFoundError("test-id"))

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "Traceback" not in result.stderr
        assert 'File "' not in result.stderr  # No file path references
        assert "line " not in result.stderr.lower()  # No line numbers


def test_error_exit_codes_are_correct_for_user_vs_internal_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should use exit code 1 for user errors, 2+ for internal errors."""
    with runner.isolated_filesystem():
        _prepare_workspace()

        # User error (TaskNotFoundError) should be exit code 1
        def _user_error_factory() -> _TaskServiceStub:
            return _TaskServiceStub(TaskNotFoundError("user-error"))

        monkeypatch.setattr(tasks_module, "_get_service", _user_error_factory)
        result = runner.invoke(app, ["task", "list"])
        assert result.exit_code == 1

        # Storage error should be exit code 3
        def _storage_error_factory() -> _TaskServiceStub:
            return _TaskServiceStub(StorageError("internal-error"))

        monkeypatch.setattr(tasks_module, "_get_service", _storage_error_factory)
        result = runner.invoke(app, ["task", "list"])
        assert result.exit_code == 3
