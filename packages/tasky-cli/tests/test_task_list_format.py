"""Tests for enhanced task list formatting."""

from pathlib import Path

import pytest
from tasky_cli.commands.projects import project_app
from tasky_cli.commands.tasks import task_app
from tasky_settings import create_task_service
from typer.testing import CliRunner


@pytest.fixture
def initialized_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an initialized project directory."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    return project_path


class TestTaskListFormatting:
    """Test suite for enhanced task list formatting."""

    def test_list_shows_status_indicators(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that status indicators are displayed correctly."""
        # Create tasks with different statuses
        runner.invoke(task_app, ["create", "Pending Task", "Still working"])
        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0
        assert "○" in result.stdout  # Pending indicator

    def test_list_shows_task_ids(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that task IDs are displayed in UUID format."""
        runner.invoke(task_app, ["create", "Test Task", "Test Details"])

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Check for UUID pattern (contains hyphens and hex characters)
        lines = result.stdout.strip().split("\n")
        task_line = next(line for line in lines if "Test Task" in line)
        # UUID should appear after status indicator and before task name
        assert "-" in task_line  # UUIDs contain hyphens
        # Extract potential UUID (second token after status indicator)
        parts = task_line.split()
        assert len(parts) >= 2  # At minimum: indicator + uuid + name...

    def test_list_output_format(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that output follows the format: {status} {id} {name} - {details}."""
        runner.invoke(task_app, ["create", "Format Test", "Check format"])

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        lines = result.stdout.strip().split("\n")
        task_line = next(line for line in lines if "Format Test" in line)

        # Check format elements
        assert "○" in task_line  # Status indicator
        assert "Format Test - Check format" in task_line  # Name - Details

    def test_list_sorting_by_status(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that tasks are sorted by status: pending → completed → cancelled."""
        # Create tasks with different statuses
        service = create_task_service()

        # Create in mixed order
        completed_task = service.create_task("Completed Task", "Done")
        service.complete_task(completed_task.task_id)

        service.create_task("Pending Task", "In progress")

        cancelled_task = service.create_task("Cancelled Task", "Not doing")
        service.cancel_task(cancelled_task.task_id)

        # List tasks
        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        lines = result.stdout.strip().split("\n")
        # Filter out summary line
        task_lines = [line for line in lines if line.strip() and not line.startswith("Showing")]

        # Check order: pending first, then completed, then cancelled
        assert "○" in task_lines[0]  # Pending first
        assert "Pending Task" in task_lines[0]

        assert "✓" in task_lines[1]  # Completed second
        assert "Completed Task" in task_lines[1]

        assert "✗" in task_lines[2]  # Cancelled third
        assert "Cancelled Task" in task_lines[2]

    def test_list_summary_line(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that summary line shows correct counts."""
        service = create_task_service()

        # Create 2 pending, 1 completed, 1 cancelled
        service.create_task("Pending 1", "Details")
        service.create_task("Pending 2", "Details")

        completed = service.create_task("Completed", "Details")
        service.complete_task(completed.task_id)

        cancelled = service.create_task("Cancelled", "Details")
        service.cancel_task(cancelled.task_id)

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Check summary line
        assert "Showing 4 tasks" in result.stdout
        assert "2 pending" in result.stdout
        assert "1 completed" in result.stdout
        assert "1 cancelled" in result.stdout

    def test_list_summary_singular_task(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that summary line uses singular 'task' for single task."""
        service = create_task_service()
        service.create_task("Single Task", "Details")

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Check singular form
        assert "Showing 1 task" in result.stdout
        assert "1 pending" in result.stdout

    def test_list_empty_shows_no_tasks_message(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that empty task list shows appropriate message."""
        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0
        assert "No tasks to display" in result.stdout
        # Should not show summary line when empty
        assert "Showing" not in result.stdout

    def test_list_empty_with_filter_shows_status_specific_message(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that empty filtered list shows status-specific message."""
        # Create only pending tasks
        runner.invoke(task_app, ["create", "Pending Task", "Details"])

        # Filter by completed (should be empty)
        result = runner.invoke(task_app, ["list", "--status", "completed"])
        assert result.exit_code == 0
        assert "No completed tasks found" in result.stdout
        # Should not show summary line when empty
        assert "Showing" not in result.stdout

    def test_list_long_flag_shows_timestamps(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that --long flag displays timestamps."""
        runner.invoke(task_app, ["create", "Timestamped Task", "Check timestamps"])

        result = runner.invoke(task_app, ["list", "--long"])
        assert result.exit_code == 0

        # Check for timestamp lines
        assert "Created:" in result.stdout
        assert "Modified:" in result.stdout
        # Check ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        assert "T" in result.stdout  # ISO format separator
        assert "Z" in result.stdout  # UTC indicator

    def test_list_long_flag_short_form(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that -l short form works for long flag."""
        runner.invoke(task_app, ["create", "Short Flag Test", "Details"])

        result = runner.invoke(task_app, ["list", "-l"])
        assert result.exit_code == 0

        assert "Created:" in result.stdout
        assert "Modified:" in result.stdout

    def test_list_without_long_flag_hides_timestamps(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that timestamps are not shown without --long flag."""
        runner.invoke(task_app, ["create", "No Timestamps", "Details"])

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Timestamps should not appear
        assert "Created:" not in result.stdout
        assert "Modified:" not in result.stdout

    def test_list_with_status_filter_shows_correct_summary(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that summary counts reflect filtered results."""
        service = create_task_service()

        # Create mixed tasks
        service.create_task("Pending 1", "Details")
        service.create_task("Pending 2", "Details")

        completed = service.create_task("Completed", "Details")
        service.complete_task(completed.task_id)

        # Filter by pending
        result = runner.invoke(task_app, ["list", "--status", "pending"])
        assert result.exit_code == 0

        # Summary should only count pending tasks
        assert "Showing 2 tasks" in result.stdout
        assert "2 pending" in result.stdout
        assert "0 completed" in result.stdout
        assert "0 cancelled" in result.stdout

    def test_list_status_indicators_for_all_statuses(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that all status indicators are correct."""
        service = create_task_service()

        # Create task for each status
        service.create_task("Pending", "Details")
        completed = service.create_task("Completed", "Details")
        service.complete_task(completed.task_id)
        cancelled = service.create_task("Cancelled", "Details")
        service.cancel_task(cancelled.task_id)

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Check all indicators present
        assert "○" in result.stdout  # Pending
        assert "✓" in result.stdout  # Completed
        assert "✗" in result.stdout  # Cancelled


class TestTaskListIntegration:
    """Integration tests for task list with real service."""

    def test_list_after_create_shows_new_task(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that newly created task appears in list with correct format."""
        # Create task
        create_result = runner.invoke(task_app, ["create", "New Task", "New Details"])
        assert create_result.exit_code == 0

        # Extract task ID from create output
        task_id_line = next(line for line in create_result.stdout.split("\n") if "ID:" in line)
        task_id = task_id_line.split("ID:")[1].strip()

        # List tasks
        list_result = runner.invoke(task_app, ["list"])
        assert list_result.exit_code == 0

        # Verify task appears with correct format
        assert "○" in list_result.stdout  # Pending indicator
        assert task_id in list_result.stdout  # Task ID
        assert "New Task - New Details" in list_result.stdout

    def test_list_after_complete_shows_completed_indicator(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that completed task shows ✓ indicator."""
        service = create_task_service()
        task = service.create_task("Complete Me", "Details")
        service.complete_task(task.task_id)

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Find the completed task line
        lines = [line for line in result.stdout.split("\n") if "Complete Me" in line]
        assert len(lines) == 1
        assert "✓" in lines[0]

    def test_list_after_cancel_shows_cancelled_indicator(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that cancelled task shows ✗ indicator."""
        service = create_task_service()
        task = service.create_task("Cancel Me", "Details")
        service.cancel_task(task.task_id)

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Find the cancelled task line
        lines = [line for line in result.stdout.split("\n") if "Cancel Me" in line]
        assert len(lines) == 1
        assert "✗" in lines[0]

    def test_list_with_many_tasks_shows_all(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that list can handle many tasks correctly."""
        service = create_task_service()

        # Create 10 tasks
        for i in range(10):
            service.create_task(f"Task {i}", f"Details {i}")

        result = runner.invoke(task_app, ["list"])
        assert result.exit_code == 0

        # Verify all tasks appear
        for i in range(10):
            assert f"Task {i}" in result.stdout

        # Verify summary
        assert "Showing 10 tasks" in result.stdout
        assert "10 pending" in result.stdout
