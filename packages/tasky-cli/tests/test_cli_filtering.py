"""End-to-end tests for task filtering CLI functionality."""

from pathlib import Path

import pytest
from tasky_cli.commands.projects import project_app
from tasky_cli.commands.tasks import task_app
from tasky_settings import create_task_service
from tasky_tasks.models import TaskModel
from typer.testing import CliRunner


@pytest.fixture
def project_with_tasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a project with mixed-status tasks."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Create tasks with different statuses
    service = create_task_service()

    # Create pending tasks
    task1 = TaskModel(name="Pending Task 1", details="Details 1")
    task2 = TaskModel(name="Pending Task 2", details="Details 2")
    service.create_task(task1.name, task1.details)
    service.create_task(task2.name, task2.details)

    # Create completed task
    task3 = service.create_task("Completed Task", "Details 3")
    service.complete_task(task3.task_id)

    # Create cancelled task
    task4 = service.create_task("Cancelled Task", "Details 4")
    service.cancel_task(task4.task_id)

    return project_path


@pytest.fixture
def project_with_no_completed_tasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a project with tasks but no completed tasks."""
    project_path = tmp_path / "test_project_no_completed"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Create only pending and cancelled tasks (no completed)
    service = create_task_service()
    task1 = TaskModel(name="Pending Task 1", details="Details 1")
    task2 = TaskModel(name="Pending Task 2", details="Details 2")
    service.create_task(task1.name, task1.details)
    service.create_task(task2.name, task2.details)

    # Create cancelled task
    task3 = service.create_task("Cancelled Task", "Details 3")
    service.cancel_task(task3.task_id)

    return project_path


class TestTaskFilteringCLI:
    """Test suite for task filtering CLI commands."""

    def test_list_all_tasks_without_filter(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test listing all tasks without status filter."""
        result = runner.invoke(task_app, ["list"])

        assert result.exit_code == 0
        assert "Pending Task 1" in result.stdout
        assert "Pending Task 2" in result.stdout
        assert "Completed Task" in result.stdout
        assert "Cancelled Task" in result.stdout

    def test_filter_by_pending_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering for pending tasks."""
        result = runner.invoke(task_app, ["list", "--status", "pending"])

        assert result.exit_code == 0
        assert "Pending Task 1" in result.stdout
        assert "Pending Task 2" in result.stdout
        assert "Completed Task" not in result.stdout
        assert "Cancelled Task" not in result.stdout

    def test_filter_by_completed_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering for completed tasks."""
        result = runner.invoke(task_app, ["list", "--status", "completed"])

        assert result.exit_code == 0
        assert "Completed Task" in result.stdout
        assert "Pending Task 1" not in result.stdout
        assert "Pending Task 2" not in result.stdout
        assert "Cancelled Task" not in result.stdout

    def test_filter_by_cancelled_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering for cancelled tasks."""
        result = runner.invoke(task_app, ["list", "--status", "cancelled"])

        assert result.exit_code == 0
        assert "Cancelled Task" in result.stdout
        assert "Pending Task 1" not in result.stdout
        assert "Completed Task" not in result.stdout

    def test_filter_with_short_option(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering using short option -s."""
        result = runner.invoke(task_app, ["list", "-s", "pending"])

        assert result.exit_code == 0
        assert "Pending Task 1" in result.stdout
        assert "Pending Task 2" in result.stdout

    def test_filter_invalid_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with invalid status shows helpful error message."""
        result = runner.invoke(task_app, ["list", "--status", "invalid"])

        assert result.exit_code == 1
        # Error message goes to stderr in CLI commands
        output = result.stdout + result.stderr

        # Verify the error message is helpful and well-formatted
        assert "Invalid status: 'invalid'" in output

        # Verify all valid statuses are mentioned with proper comma-space separation
        expected_formats = [
            "cancelled, completed, pending",
            "pending, completed, cancelled",
        ]
        assert any(fmt in output for fmt in expected_formats)
        # Verify we have comma-space (not just comma) for readability
        assert ", " in output

    def test_filter_case_insensitive(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering is case-insensitive."""
        result_upper = runner.invoke(task_app, ["list", "--status", "PENDING"])
        result_mixed = runner.invoke(task_app, ["list", "--status", "Pending"])

        assert result_upper.exit_code == 0
        assert result_mixed.exit_code == 0
        assert "Pending Task 1" in result_upper.stdout
        assert "Pending Task 1" in result_mixed.stdout

    def test_filter_empty_results(
        self,
        runner: CliRunner,
        project_with_no_completed_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with no matching tasks shows appropriate message."""
        result = runner.invoke(task_app, ["list", "--status", "completed"])

        assert result.exit_code == 0
        assert "No completed tasks found" in result.stdout

    def test_help_shows_status_option(self, runner: CliRunner) -> None:
        """Test that help text documents the status option."""
        result = runner.invoke(task_app, ["list", "--help"])

        assert result.exit_code == 0
        assert "--status" in result.stdout
        assert "-s" in result.stdout
        # Help text wraps the option description
        assert "pending" in result.stdout
        assert "completed" in result.stdout
        assert "cancelled" in result.stdout

    def test_filter_empty_string_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with empty string status shows error."""
        result = runner.invoke(task_app, ["list", "--status", ""])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid status" in output

    def test_filter_whitespace_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with whitespace-padded status is rejected (intentional behavior)."""
        # Whitespace is NOT stripped from status input by design.
        # This is intentional: users must provide exact status values (pending, completed, cancelled).
        # Rejecting " pending " helps catch typos and accidental whitespace in user input.
        result = runner.invoke(task_app, ["list", "--status", " pending "])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid status" in output

    def test_filter_very_long_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with very long status string shows error."""
        long_status = "pending" * 100
        result = runner.invoke(task_app, ["list", "--status", long_status])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid status" in output

    def test_filter_numeric_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with numeric status shows error."""
        result = runner.invoke(task_app, ["list", "--status", "123"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid status" in output

    def test_filter_special_characters_status(
        self,
        runner: CliRunner,
        project_with_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering with special characters shows error."""
        result = runner.invoke(task_app, ["list", "--status", "pending!@#"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid status" in output
