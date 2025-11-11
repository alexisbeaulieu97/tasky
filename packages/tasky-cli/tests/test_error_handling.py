"""Tests for CLI error handling and presentation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tasky_cli import app
from tasky_cli.commands import tasks as tasks_module
from tasky_storage.errors import StorageConfigurationError
from tasky_tasks import TaskNotFoundError
from typer.testing import CliRunner

runner = CliRunner()


class _TaskServiceStub:
    """Task service stub that raises a configured exception."""

    def __init__(self, error: Exception | None = None, tasks: list[str] | None = None) -> None:
        self._error = error
        self._tasks = tasks or []

    def get_all_tasks(self) -> list[str]:
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
        monkeypatch.setattr(
            tasks_module,
            "_create_task_service",
            lambda _: _TaskServiceStub(TaskNotFoundError("abc")),
        )

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 1
        assert "Error: Task 'abc' not found." in result.stderr
        assert "Suggestion: Run 'tasky task list' to view available tasks." in result.stderr
        assert "Traceback" not in result.stderr


def test_storage_error_results_in_exit_code_three(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI should map storage failures to exit code 3."""
    with runner.isolated_filesystem():
        _prepare_workspace()
        monkeypatch.setattr(
            tasks_module,
            "_create_task_service",
            lambda _: _TaskServiceStub(StorageConfigurationError("boom")),
        )

        result = runner.invoke(app, ["task", "list"])

        assert result.exit_code == 3
        assert "Storage failure encountered." in result.stderr


def test_invalid_storage_data_triggers_error_without_patch() -> None:
    """Invalid storage documents should surface as storage failures."""
    with runner.isolated_filesystem():
        storage_root = Path(".tasky")
        storage_root.mkdir(exist_ok=True)
        invalid_document = {
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
        monkeypatch.setattr(
            tasks_module,
            "_create_task_service",
            lambda _: _TaskServiceStub(TaskNotFoundError("xyz")),
        )

        result = runner.invoke(app, ["task", "--verbose", "list"])

        assert result.exit_code == 1
        assert "Traceback (most recent call last)" in result.stderr

