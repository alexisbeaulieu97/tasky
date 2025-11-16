"""Tests for task create command."""

from pathlib import Path

import pytest
from tasky_cli.commands.tasks import task_app
from tasky_settings import create_task_service
from typer.testing import CliRunner


class TestTaskCreateCommand:
    """Test suite for task create command."""

    def test_create_task_success(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test successful task creation."""
        result = runner.invoke(task_app, ["create", "Test Task", "Test Details"])

        assert result.exit_code == 0
        assert "Task created successfully!" in result.stdout
        assert "ID:" in result.stdout
        assert "Name: Test Task" in result.stdout
        assert "Details: Test Details" in result.stdout
        assert "Status: PENDING" in result.stdout
        assert "Created:" in result.stdout

    def test_create_task_persists_to_storage(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that created task is actually persisted."""
        # Create a task
        result = runner.invoke(task_app, ["create", "Persisted Task", "Should be saved"])
        assert result.exit_code == 0

        # Verify it appears in the list
        list_result = runner.invoke(task_app, ["list"])
        assert list_result.exit_code == 0
        assert "Persisted Task" in list_result.stdout
        assert "Should be saved" in list_result.stdout

    def test_create_task_with_special_characters(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test task creation with special characters in name and details."""
        result = runner.invoke(
            task_app,
            ["create", "Task with 'quotes' & symbols", "Details: $100 @ 50%"],
        )

        assert result.exit_code == 0
        assert "Task created successfully!" in result.stdout
        assert "Task with 'quotes' & symbols" in result.stdout
        assert "Details: $100 @ 50%" in result.stdout

    def test_create_task_with_long_strings(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test task creation with long name and details."""
        long_name = "A" * 200
        long_details = "B" * 500

        result = runner.invoke(task_app, ["create", long_name, long_details])

        assert result.exit_code == 0
        assert "Task created successfully!" in result.stdout
        assert long_name in result.stdout
        assert long_details in result.stdout

    def test_create_multiple_tasks(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test creating multiple tasks sequentially."""
        # Create first task
        result1 = runner.invoke(task_app, ["create", "Task 1", "Details 1"])
        assert result1.exit_code == 0

        # Create second task
        result2 = runner.invoke(task_app, ["create", "Task 2", "Details 2"])
        assert result2.exit_code == 0

        # Create third task
        result3 = runner.invoke(task_app, ["create", "Task 3", "Details 3"])
        assert result3.exit_code == 0

        # Verify all tasks exist
        list_result = runner.invoke(task_app, ["list"])
        assert "Task 1" in list_result.stdout
        assert "Task 2" in list_result.stdout
        assert "Task 3" in list_result.stdout

    def test_create_task_assigns_unique_ids(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that each created task gets a unique ID."""
        result1 = runner.invoke(task_app, ["create", "Task A", "Details A"])
        result2 = runner.invoke(task_app, ["create", "Task B", "Details B"])

        # Extract IDs from output
        id1 = next(
            (line for line in result1.stdout.split("\n") if line.startswith("ID:")),
            None,
        )
        id2 = next(
            (line for line in result2.stdout.split("\n") if line.startswith("ID:")),
            None,
        )

        assert id1 is not None, "Task 1 output missing ID line"
        assert id2 is not None, "Task 2 output missing ID line"
        assert id1 != id2

    def test_create_task_sets_pending_status(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that newly created tasks have PENDING status."""
        result = runner.invoke(task_app, ["create", "New Task", "Details"])

        assert result.exit_code == 0
        assert "Status: PENDING" in result.stdout

        # Verify with service layer
        service = create_task_service()
        tasks = service.get_all_tasks()
        assert len(tasks) == 1
        # All newly created tasks should have pending status
        assert all(task.status.value == "pending" for task in tasks)

    def test_create_task_with_empty_name(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that empty name is rejected with clear error message."""
        result = runner.invoke(task_app, ["create", "", "Details"])

        assert result.exit_code != 0
        # Error messages are written to stderr
        assert "name cannot be empty" in result.stderr.lower()

    def test_create_task_with_empty_details(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that empty details are rejected with clear error message."""
        result = runner.invoke(task_app, ["create", "Task Name", ""])

        assert result.exit_code != 0
        assert "details cannot be empty" in result.stderr.lower()

    def test_create_task_with_whitespace_only_name(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that whitespace-only name is rejected."""
        result = runner.invoke(task_app, ["create", "   ", "Details"])

        assert result.exit_code != 0
        assert "name cannot be empty" in result.stderr.lower()

    def test_create_task_output_format(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that output format matches expected structure."""
        result = runner.invoke(task_app, ["create", "Format Test", "Check output"])

        assert result.exit_code == 0

        lines = result.stdout.strip().split("\n")
        assert any("Task created successfully!" in line for line in lines)
        assert any(line.startswith("ID:") for line in lines)
        assert any(line.startswith("Name:") for line in lines)
        assert any(line.startswith("Details:") for line in lines)
        assert any(line.startswith("Status:") for line in lines)
        assert any(line.startswith("Created:") for line in lines)


class TestTaskCreateErrors:
    """Test error handling for task create command."""

    def test_create_task_missing_name_argument(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error when NAME argument is missing."""
        result = runner.invoke(task_app, ["create"])

        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "Missing argument" in result.stderr

    def test_create_task_missing_details_argument(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test error when DETAILS argument is missing."""
        result = runner.invoke(task_app, ["create", "Task Name"])

        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "Missing argument" in result.stderr

    def test_create_task_without_project(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error when attempting to create task outside a project."""
        # Change to a directory without an initialized project
        no_project_path = tmp_path / "no_project"
        no_project_path.mkdir()
        monkeypatch.chdir(no_project_path)

        result = runner.invoke(task_app, ["create", "Task", "Details"])

        assert result.exit_code != 0
        assert "No project found" in result.stderr

    def test_create_task_help_displays_correctly(
        self,
        runner: CliRunner,
    ) -> None:
        """Test that help text displays correctly for create command."""
        result = runner.invoke(task_app, ["create", "--help"])

        assert result.exit_code == 0
        assert "Create a new task" in result.stdout
        assert "NAME" in result.stdout
        assert "DETAILS" in result.stdout
        assert "Examples:" in result.stdout


class TestTaskCreateErrorCases:
    """Test error handling for task create command."""

    def test_create_task_missing_name(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that creating task without name fails."""
        result = runner.invoke(task_app, ["create"])

        assert result.exit_code != 0
        assert "Missing argument" in result.stderr or "required" in result.stderr.lower()

    def test_create_task_empty_name_string(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that creating task with empty name fails validation."""
        result = runner.invoke(task_app, ["create", "", "Details"])

        # Empty string should be caught as validation error
        assert result.exit_code != 0

    def test_create_task_missing_details(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that creating task without details fails."""
        result = runner.invoke(task_app, ["create", "Task Name"])

        assert result.exit_code != 0
        assert "Missing argument" in result.stderr or "required" in result.stderr.lower()

    def test_create_task_with_very_long_name(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test creating task with extremely long name."""
        # Test with 1000+ character name
        very_long_name = "A" * 1500
        result = runner.invoke(task_app, ["create", very_long_name, "Details"])

        # Should either succeed or fail gracefully
        if result.exit_code != 0:
            assert "Error" in result.stderr
        else:
            # If it succeeds, verify the task was created
            assert "Task created successfully" in result.stdout

    def test_create_task_storage_write_fails(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling when storage write fails."""
        from tasky_cli.commands import tasks as tasks_module  # noqa: PLC0415
        from tasky_storage.errors import StorageError  # noqa: PLC0415

        class _FailingTaskService:
            def create_task(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
                raise StorageError("Disk full")  # noqa: EM101, TRY003

        def _factory() -> _FailingTaskService:
            return _FailingTaskService()

        monkeypatch.setattr(tasks_module, "_get_service", _factory)

        result = runner.invoke(task_app, ["create", "Task", "Details"])

        assert result.exit_code == 3  # Storage error exit code
        assert "Storage failure" in result.stderr

    def test_create_task_project_not_found(
        self,
        runner: CliRunner,
    ) -> None:
        """Test that creating task without initialized project fails."""
        with runner.isolated_filesystem():
            result = runner.invoke(task_app, ["create", "Task", "Details"])

            assert result.exit_code != 0
            assert "No project found" in result.stderr or "project init" in result.stderr.lower()


class TestTaskCreateIntegration:
    """Integration tests for task create with other commands."""

    def test_create_then_complete_workflow(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test creating a task and then completing it."""
        # Create task
        create_result = runner.invoke(task_app, ["create", "Workflow Task", "Test workflow"])
        assert create_result.exit_code == 0

        # Extract task ID
        id_line = next(
            (line for line in create_result.stdout.split("\n") if line.startswith("ID:")),
            None,
        )
        assert id_line is not None, "Create output missing ID line"
        task_id = id_line.split("ID:")[1].strip()

        # Complete the task
        complete_result = runner.invoke(task_app, ["complete", task_id])
        assert complete_result.exit_code == 0

    def test_create_and_filter_by_status(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
    ) -> None:
        """Test creating tasks and filtering by pending status."""
        # Create multiple tasks
        runner.invoke(task_app, ["create", "Task 1", "Details 1"])
        runner.invoke(task_app, ["create", "Task 2", "Details 2"])

        # Filter by pending status
        list_result = runner.invoke(task_app, ["list", "--status", "pending"])

        assert list_result.exit_code == 0
        assert "Task 1" in list_result.stdout
        assert "Task 2" in list_result.stdout
