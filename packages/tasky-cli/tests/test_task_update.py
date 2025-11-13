"""Tests for task update command."""

import time
from pathlib import Path
from uuid import UUID

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
def task_id(runner: CliRunner, initialized_project: Path) -> str:  # noqa: ARG001
    """Create a task and return its ID."""
    result = runner.invoke(task_app, ["create", "Original Name", "Original Details"])
    assert result.exit_code == 0

    # Extract task ID from output
    for line in result.stdout.split("\n"):
        if line.startswith("ID:"):
            return line.split("ID:")[1].strip()

    msg = "Failed to extract task ID from create command output"
    raise ValueError(msg)


class TestTaskUpdateCommand:
    """Test suite for task update command."""

    def test_update_name_only(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating only the task name."""
        result = runner.invoke(task_app, ["update", task_id, "--name", "Updated Name"])

        assert result.exit_code == 0
        assert "Task updated successfully!" in result.stdout
        assert "Name: Updated Name" in result.stdout
        assert "Details: Original Details" in result.stdout
        assert "Status: PENDING" in result.stdout
        assert "Modified:" in result.stdout

    def test_update_details_only(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating only the task details."""
        result = runner.invoke(task_app, ["update", task_id, "--details", "Updated Details"])

        assert result.exit_code == 0
        assert "Task updated successfully!" in result.stdout
        assert "Name: Original Name" in result.stdout
        assert "Details: Updated Details" in result.stdout
        assert "Status: PENDING" in result.stdout

    def test_update_both_fields(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating both name and details."""
        result = runner.invoke(
            task_app,
            ["update", task_id, "--name", "New Name", "--details", "New Details"],
        )

        assert result.exit_code == 0
        assert "Task updated successfully!" in result.stdout
        assert "Name: New Name" in result.stdout
        assert "Details: New Details" in result.stdout

    def test_update_persists_to_storage(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that updates are persisted to storage."""
        # Update the task
        result = runner.invoke(task_app, ["update", task_id, "--name", "Persisted Name"])
        assert result.exit_code == 0

        # Verify change persisted by listing tasks
        list_result = runner.invoke(task_app, ["list"])
        assert "Persisted Name" in list_result.stdout
        assert "Original Details" in list_result.stdout

        # Verify with service layer
        service = create_task_service()
        tasks = service.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].name == "Persisted Name"
        assert tasks[0].details == "Original Details"

    def test_update_multiple_times(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating a task multiple times."""
        # First update
        result1 = runner.invoke(task_app, ["update", task_id, "--name", "First Update"])
        assert result1.exit_code == 0
        assert "Name: First Update" in result1.stdout

        # Second update
        result2 = runner.invoke(task_app, ["update", task_id, "--name", "Second Update"])
        assert result2.exit_code == 0
        assert "Name: Second Update" in result2.stdout

        # Third update
        result3 = runner.invoke(
            task_app,
            ["update", task_id, "--name", "Third", "--details", "Third Details"],
        )
        assert result3.exit_code == 0
        assert "Name: Third" in result3.stdout
        assert "Details: Third Details" in result3.stdout

    def test_update_with_special_characters(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating with special characters."""
        result = runner.invoke(
            task_app,
            [
                "update",
                task_id,
                "--name",
                "Name with 'quotes' & symbols",
                "--details",
                "Price: $100 @ 50%",
            ],
        )

        assert result.exit_code == 0
        assert "Name with 'quotes' & symbols" in result.stdout
        assert "Price: $100 @ 50%" in result.stdout

    def test_update_with_long_strings(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test updating with long strings."""
        long_name = "A" * 200
        long_details = "B" * 500

        result = runner.invoke(
            task_app,
            ["update", task_id, "--name", long_name, "--details", long_details],
        )

        assert result.exit_code == 0
        assert long_name in result.stdout
        assert long_details in result.stdout

    def test_update_preserves_status(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that updating doesn't change task status."""
        # Complete the task
        complete_result = runner.invoke(task_app, ["complete", task_id])
        assert complete_result.exit_code == 0

        # Update the task
        update_result = runner.invoke(task_app, ["update", task_id, "--name", "Updated"])
        assert update_result.exit_code == 0
        assert "Status: COMPLETED" in update_result.stdout

    def test_update_updates_modified_timestamp(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that update command updates the modified timestamp."""
        # Get the task via service layer to check original timestamp
        service = create_task_service()
        original_task = service.get_task(UUID(task_id))
        original_timestamp = original_task.updated_at

        # Wait a tiny bit and update
        time.sleep(0.01)

        result = runner.invoke(task_app, ["update", task_id, "--name", "Updated"])
        assert result.exit_code == 0

        # Check that timestamp changed
        updated_task = service.get_task(UUID(task_id))
        assert updated_task.updated_at > original_timestamp


class TestTaskUpdateErrorHandling:
    """Test error handling for task update command."""

    def test_update_without_flags(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test error when neither --name nor --details is provided."""
        result = runner.invoke(task_app, ["update", task_id])

        assert result.exit_code == 1
        assert "At least one of --name or --details must be provided" in result.stderr

    def test_update_missing_task_id(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error when task ID is not provided."""
        result = runner.invoke(task_app, ["update", "--name", "Test"])

        assert result.exit_code != 0
        # Typer shows missing argument error

    def test_update_invalid_uuid_format(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error with invalid UUID format."""
        result = runner.invoke(task_app, ["update", "not-a-uuid", "--name", "Test"])

        assert result.exit_code == 1
        # Error messages are written to stdout by typer.echo()
        assert "Invalid UUID format" in result.stdout or "Invalid UUID format" in result.stderr

    def test_update_nonexistent_task(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error when task ID doesn't exist."""
        nonexistent_id = "123e4567-e89b-12d3-a456-426614174000"
        result = runner.invoke(task_app, ["update", nonexistent_id, "--name", "Test"])

        assert result.exit_code == 1
        assert f"Task '{nonexistent_id}' not found" in result.stderr

    def test_update_with_empty_name(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test error when updating with empty name."""
        result = runner.invoke(task_app, ["update", task_id, "--name", ""])

        assert result.exit_code != 0
        assert "name cannot be empty" in result.stderr.lower()

    def test_update_with_empty_details(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test error when updating with empty details."""
        result = runner.invoke(task_app, ["update", task_id, "--details", ""])

        assert result.exit_code != 0
        assert "details cannot be empty" in result.stderr.lower()

    def test_update_with_whitespace_only_name(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test error when updating with whitespace-only name."""
        result = runner.invoke(task_app, ["update", task_id, "--name", "   "])

        assert result.exit_code != 0
        assert "name cannot be empty" in result.stderr.lower()


class TestTaskUpdateFieldIsolation:
    """Test that update command properly isolates field changes."""

    def test_name_update_preserves_details(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that updating name doesn't change details."""
        # Update name
        result = runner.invoke(task_app, ["update", task_id, "--name", "New Name"])
        assert result.exit_code == 0

        # Verify details unchanged via service
        service = create_task_service()
        task = service.get_task(UUID(task_id))
        assert task.name == "New Name"
        assert task.details == "Original Details"

    def test_details_update_preserves_name(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that updating details doesn't change name."""
        # Update details
        result = runner.invoke(task_app, ["update", task_id, "--details", "New Details"])
        assert result.exit_code == 0

        # Verify name unchanged via service
        service = create_task_service()
        task = service.get_task(UUID(task_id))
        assert task.name == "Original Name"
        assert task.details == "New Details"

    def test_sequential_isolated_updates(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test multiple isolated updates in sequence."""
        # Update name
        result1 = runner.invoke(task_app, ["update", task_id, "--name", "Name v1"])
        assert result1.exit_code == 0

        # Update details
        result2 = runner.invoke(task_app, ["update", task_id, "--details", "Details v1"])
        assert result2.exit_code == 0

        # Update name again
        result3 = runner.invoke(task_app, ["update", task_id, "--name", "Name v2"])
        assert result3.exit_code == 0

        # Verify final state
        service = create_task_service()
        task = service.get_task(UUID(task_id))
        assert task.name == "Name v2"
        assert task.details == "Details v1"


class TestTaskUpdateOutputFormat:
    """Test that update command output follows expected format."""

    def test_output_includes_all_fields(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that output includes all expected fields."""
        result = runner.invoke(task_app, ["update", task_id, "--name", "Test"])

        assert result.exit_code == 0
        lines = result.stdout.split("\n")

        # Check for expected output structure
        assert any("Task updated successfully!" in line for line in lines)
        assert any(line.startswith("ID:") for line in lines)
        assert any(line.startswith("Name:") for line in lines)
        assert any(line.startswith("Details:") for line in lines)
        assert any(line.startswith("Status:") for line in lines)
        assert any(line.startswith("Modified:") for line in lines)

    def test_output_shows_updated_values(
        self,
        runner: CliRunner,
        task_id: str,
    ) -> None:
        """Test that output displays the new values after update."""
        result = runner.invoke(
            task_app,
            ["update", task_id, "--name", "Updated Name", "--details", "Updated Details"],
        )

        assert result.exit_code == 0
        assert f"ID: {task_id}" in result.stdout
        assert "Name: Updated Name" in result.stdout
        assert "Details: Updated Details" in result.stdout
