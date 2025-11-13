"""Tests for task show command."""

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


@pytest.fixture
def task_with_id(
    runner: CliRunner,
    initialized_project: Path,  # noqa: ARG001
) -> str:
    """Create a task and return its ID."""
    result = runner.invoke(task_app, ["create", "Test Task", "Test Details"])
    assert result.exit_code == 0

    # Extract task ID from output
    for line in result.stdout.split("\n"):
        if line.startswith("ID:"):
            return line.split("ID:")[1].strip()

    pytest.fail("Could not extract task ID from create output")


class TestTaskShowCommand:
    """Test suite for task show command."""

    def test_show_task_success(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test successful task retrieval and display."""
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        assert "Task Details" in result.stdout
        assert f"ID: {task_with_id}" in result.stdout
        assert "Name: Test Task" in result.stdout
        assert "Details: Test Details" in result.stdout
        assert "Status: PENDING" in result.stdout
        assert "Created:" in result.stdout
        assert "Updated:" in result.stdout

    def test_show_task_displays_all_metadata(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test that all task metadata fields are displayed."""
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        # Verify all required fields are present
        required_fields = ["ID:", "Name:", "Details:", "Status:", "Created:", "Updated:"]
        for field in required_fields:
            assert field in result.stdout, f"Missing field: {field}"

    def test_show_task_with_special_characters(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test showing task with special characters in name and details."""
        # Create task with special characters
        create_result = runner.invoke(
            task_app,
            ["create", "Task with 'quotes' & symbols", "Details: $100 @ 50%"],
        )
        assert create_result.exit_code == 0

        # Extract task ID
        task_id = None
        for line in create_result.stdout.split("\n"):
            if line.startswith("ID:"):
                task_id = line.split("ID:")[1].strip()
                break
        assert task_id is not None

        # Show the task
        result = runner.invoke(task_app, ["show", task_id])

        assert result.exit_code == 0
        assert "Task with 'quotes' & symbols" in result.stdout
        assert "Details: $100 @ 50%" in result.stdout

    def test_show_task_with_long_strings(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test showing task with long name and details."""
        long_name = "A" * 200
        long_details = "B" * 500

        # Create task with long strings
        create_result = runner.invoke(task_app, ["create", long_name, long_details])
        assert create_result.exit_code == 0

        # Extract task ID
        task_id = None
        for line in create_result.stdout.split("\n"):
            if line.startswith("ID:"):
                task_id = line.split("ID:")[1].strip()
                break
        assert task_id is not None

        # Show the task
        result = runner.invoke(task_app, ["show", task_id])

        assert result.exit_code == 0
        assert long_name in result.stdout
        assert long_details in result.stdout

    def test_show_completed_task(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test showing a completed task displays COMPLETED status."""
        # Complete the task
        complete_result = runner.invoke(task_app, ["complete", task_with_id])
        assert complete_result.exit_code == 0

        # Show the completed task
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        assert "Status: COMPLETED" in result.stdout

    def test_show_cancelled_task(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test showing a cancelled task displays CANCELLED status."""
        # Cancel the task
        cancel_result = runner.invoke(task_app, ["cancel", task_with_id])
        assert cancel_result.exit_code == 0

        # Show the cancelled task
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        assert "Status: CANCELLED" in result.stdout

    def test_show_task_timestamps_consistency(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test that timestamps are displayed in consistent format."""
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        # Timestamps should be in YYYY-MM-DD HH:MM:SS format
        output = result.stdout
        # Look for lines with "Created:" and "Updated:"
        created_line = next((line for line in output.split("\n") if "Created:" in line), "")
        updated_line = next((line for line in output.split("\n") if "Updated:" in line), "")

        # Basic format check - should have date and time
        assert len(created_line.split()) >= 3  # "Created: YYYY-MM-DD HH:MM:SS"
        assert len(updated_line.split()) >= 3  # "Updated: YYYY-MM-DD HH:MM:SS"


class TestTaskShowCommandErrors:
    """Test suite for task show command error handling."""

    def test_show_task_with_invalid_uuid(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error message for invalid UUID format."""
        result = runner.invoke(task_app, ["show", "not-a-uuid"])

        assert result.exit_code == 1
        assert "Invalid UUID format" in result.stderr
        assert "Expected format:" in result.stderr
        assert "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" in result.stderr

    def test_show_task_with_nonexistent_id(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error message for non-existent task ID."""
        # Use a valid UUID that doesn't exist
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        result = runner.invoke(task_app, ["show", nonexistent_id])

        assert result.exit_code == 1
        assert "not found" in result.stderr
        assert nonexistent_id in result.stderr

    def test_show_task_missing_argument(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error message when task ID argument is missing."""
        result = runner.invoke(task_app, ["show"])

        assert result.exit_code == 2  # Typer exits with 2 for usage errors
        output = result.stdout + result.stderr
        assert "Missing argument" in output

    def test_show_task_without_project(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error message when no project is initialized."""
        # Change to a directory without a project
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        result = runner.invoke(task_app, ["show", "00000000-0000-0000-0000-000000000000"])

        assert result.exit_code == 1
        assert "No project found" in result.stderr


class TestTaskShowCommandIntegration:
    """Integration tests for task show command."""

    def test_show_task_after_multiple_operations(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        task_with_id: str,
    ) -> None:
        """Test showing task after multiple state changes."""
        # Complete the task
        runner.invoke(task_app, ["complete", task_with_id])

        # Reopen the task
        runner.invoke(task_app, ["reopen", task_with_id])

        # Show the task - should be PENDING again
        result = runner.invoke(task_app, ["show", task_with_id])

        assert result.exit_code == 0
        assert "Status: PENDING" in result.stdout

    def test_show_multiple_tasks_sequentially(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test showing multiple tasks one after another."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            result = runner.invoke(task_app, ["create", f"Task {i}", f"Details {i}"])
            assert result.exit_code == 0
            # Extract task ID
            for line in result.stdout.split("\n"):
                if line.startswith("ID:"):
                    task_ids.append(line.split("ID:")[1].strip())
                    break

        # Show each task and verify correct details
        for i, task_id in enumerate(task_ids):
            result = runner.invoke(task_app, ["show", task_id])
            assert result.exit_code == 0
            assert f"Name: Task {i}" in result.stdout
            assert f"Details: Details {i}" in result.stdout

    def test_show_task_retrieved_from_list(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test showing a task using ID from list command output."""
        # Create a task
        create_result = runner.invoke(task_app, ["create", "Listed Task", "Listed Details"])
        assert create_result.exit_code == 0

        # Get task list
        list_result = runner.invoke(task_app, ["list"])
        assert list_result.exit_code == 0

        # Extract task ID from list output (second column in list format)
        list_lines = [line for line in list_result.stdout.split("\n") if "Listed Task" in line]
        assert len(list_lines) > 0
        # List format: "○ {uuid} {name} - {details}"
        parts = list_lines[0].split()
        task_id = parts[1]  # UUID is the second part after the indicator

        # Show the task using the ID from list
        result = runner.invoke(task_app, ["show", task_id])

        assert result.exit_code == 0
        assert "Name: Listed Task" in result.stdout
        assert "Details: Listed Details" in result.stdout

    def test_show_task_with_real_service(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that show command uses real task service correctly."""
        # Create a task directly using the service
        service = create_task_service()
        task = service.create_task("Service Task", "Created via service")

        # Show the task using CLI
        result = runner.invoke(task_app, ["show", str(task.task_id)])

        assert result.exit_code == 0
        assert f"ID: {task.task_id}" in result.stdout
        assert "Name: Service Task" in result.stdout
        assert "Details: Created via service" in result.stdout
        assert "Status: PENDING" in result.stdout
