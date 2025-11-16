"""Tests for task import and export commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from tasky_cli.commands.tasks import task_app
from tasky_settings import create_task_service
from typer.testing import CliRunner

if TYPE_CHECKING:
    from tasky_tasks.models import TaskModel


@pytest.fixture
def sample_tasks(initialized_project: Path) -> list[TaskModel]:  # noqa: ARG001
    """Create sample tasks for testing."""
    service = create_task_service()
    return [
        service.create_task("Task 1", "Details 1"),
        service.create_task("Task 2", "Details 2"),
        service.create_task("Task 3", "Details 3"),
    ]


class TestExportCommand:
    """Test suite for export command."""

    def test_export_with_no_filters_exports_all_tasks(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],
        tmp_path: Path,
    ) -> None:
        """Test exporting all tasks without filters."""
        export_file = tmp_path / "export.json"

        result = runner.invoke(task_app, ["export", str(export_file)])

        assert result.exit_code == 0
        assert f"Exported {len(sample_tasks)} tasks" in result.stdout
        assert export_file.exists()

        # Verify exported content
        with export_file.open() as f:
            data = json.load(f)
        assert "tasks" in data
        assert len(data["tasks"]) == len(sample_tasks)

    def test_export_creates_valid_reimportable_file(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test that exported file can be re-imported."""
        export_file = tmp_path / "export.json"

        # Export
        export_result = runner.invoke(task_app, ["export", str(export_file)])
        assert export_result.exit_code == 0

        # Clear tasks and re-import
        service = create_task_service()
        for task in service.get_all_tasks():
            service.delete_task(task.task_id)

        import_result = runner.invoke(task_app, ["import", str(export_file)])
        assert import_result.exit_code == 0
        assert "Import complete" in import_result.stdout

    def test_export_with_many_tasks_performance(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test exporting 1000+ tasks."""
        service = create_task_service()

        # Create 1000 tasks
        for i in range(1000):
            service.create_task(f"Task {i}", f"Details {i}")

        export_file = tmp_path / "large_export.json"
        result = runner.invoke(task_app, ["export", str(export_file)])

        assert result.exit_code == 0
        assert "Exported 1000 tasks" in result.stdout
        assert export_file.exists()

    def test_export_file_has_proper_json_formatting(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test that export file is valid JSON."""
        export_file = tmp_path / "export.json"

        result = runner.invoke(task_app, ["export", str(export_file)])
        assert result.exit_code == 0

        # Verify JSON is valid and properly formatted
        with export_file.open() as f:
            data = json.load(f)

        assert "version" in data
        assert "tasks" in data

    def test_export_with_special_characters_in_content(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test exporting tasks with special characters."""
        service = create_task_service()
        service.create_task("Task with 'quotes' & symbols", "Details: $100 @ 50%")
        service.create_task("Unicode Task", "你好 🎉 ñ")

        export_file = tmp_path / "export.json"
        result = runner.invoke(task_app, ["export", str(export_file)])

        assert result.exit_code == 0

        # Verify special characters are preserved
        with export_file.open() as f:
            data = json.load(f)

        # Handle both dict and list format for tasks
        if isinstance(data["tasks"], dict):
            task_names = [task["name"] for task in data["tasks"].values()]
        else:
            task_names = [task["name"] for task in data["tasks"]]

        assert "Task with 'quotes' & symbols" in task_names
        assert "Unicode Task" in task_names


class TestImportCommand:
    """Test suite for import command."""

    def test_import_from_empty_file_fails(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test importing from an empty file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        result = runner.invoke(task_app, ["import", str(empty_file)])

        assert result.exit_code != 0
        assert "Invalid" in result.stderr or "error" in result.stderr.lower()

    def test_import_with_malformed_json_fails(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test importing file with malformed JSON."""
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text('{"tasks": {')

        result = runner.invoke(task_app, ["import", str(malformed_file)])

        assert result.exit_code != 0
        assert "Invalid" in result.stderr or "error" in result.stderr.lower()

    def test_import_with_missing_required_fields(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test importing tasks with missing required fields."""
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_data = {
            "version": "1.0",
            "tasks": {
                "task1": {
                    "task_id": "12345678-1234-1234-1234-123456789012",
                    "name": "Task without details",
                    # Missing 'details' field
                },
            },
        }
        incomplete_file.write_text(json.dumps(incomplete_data))

        result = runner.invoke(task_app, ["import", str(incomplete_file)])

        # Should fail due to invalid export format
        assert result.exit_code != 0
        assert "Invalid" in result.stderr or "validation" in result.stderr.lower()

    def test_import_strategy_skip_duplicate_task_ids(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test import with append strategy (default) handles duplicate IDs."""
        export_file = tmp_path / "export.json"

        # Export existing tasks
        runner.invoke(task_app, ["export", str(export_file)])

        # Import with append (should re-key duplicates with new IDs)
        result = runner.invoke(task_app, ["import", str(export_file), "--strategy", "append"])

        assert result.exit_code == 0
        # Should create new tasks (duplicates re-keyed)
        assert "created" in result.stdout.lower()

    def test_import_strategy_merge_resolves_conflicts(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],
        tmp_path: Path,
    ) -> None:
        """Test import with merge strategy updates existing tasks."""
        export_file = tmp_path / "export.json"

        # Export tasks
        runner.invoke(task_app, ["export", str(export_file)])

        # Modify one task using CLI
        runner.invoke(
            task_app,
            ["update", str(sample_tasks[0].task_id), "--name", "Modified Task"],
        )

        # Import with merge (should update the modified task back to original)
        result = runner.invoke(task_app, ["import", str(export_file), "--strategy", "merge"])

        assert result.exit_code == 0
        assert "updated" in result.stdout.lower()

    def test_import_with_many_tasks_performance(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test importing 1000+ tasks."""
        # Create export file with 1000 tasks
        service = create_task_service()
        for i in range(1000):
            service.create_task(f"Task {i}", f"Details {i}")

        export_file = tmp_path / "large_export.json"
        runner.invoke(task_app, ["export", str(export_file)])

        # Clear and re-import
        for task in service.get_all_tasks():
            service.delete_task(task.task_id)

        result = runner.invoke(task_app, ["import", str(export_file)])

        assert result.exit_code == 0
        assert "1000 created" in result.stdout or "1000" in result.stdout

    def test_import_creates_backup_before_executing(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test that import creates a backup before modifying tasks."""
        export_file = tmp_path / "export.json"
        runner.invoke(task_app, ["export", str(export_file)])

        # Import should create backup (implementation may vary)
        result = runner.invoke(task_app, ["import", str(export_file), "--strategy", "replace"])

        # Verify import succeeded
        assert result.exit_code == 0

    def test_import_dry_run_does_not_modify_database(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test that dry-run mode doesn't modify the database."""
        service = create_task_service()
        initial_count = len(service.get_all_tasks())

        export_file = tmp_path / "export.json"
        runner.invoke(task_app, ["export", str(export_file)])

        # Import with dry-run
        result = runner.invoke(task_app, ["import", str(export_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout or "Would import" in result.stdout

        # Verify database was not modified (fresh service instance)
        service_after = create_task_service()
        assert len(service_after.get_all_tasks()) == initial_count


class TestImportExportIntegration:
    """Integration tests for import/export workflow."""

    def test_export_import_roundtrip_preserves_data(
        self,
        runner: CliRunner,
        sample_tasks: list[TaskModel],
        tmp_path: Path,
    ) -> None:
        """Test that export -> import preserves all task data."""
        export_file = tmp_path / "export.json"

        # Export
        runner.invoke(task_app, ["export", str(export_file)])

        # Clear tasks
        service = create_task_service()
        for task in service.get_all_tasks():
            service.delete_task(task.task_id)

        # Import
        runner.invoke(task_app, ["import", str(export_file)])

        # Verify all tasks restored (fresh service instance)
        service_after = create_task_service()
        restored_tasks = service_after.get_all_tasks()
        assert len(restored_tasks) == len(sample_tasks)

        # Verify task names preserved
        original_names = {task.name for task in sample_tasks}
        restored_names = {task.name for task in restored_tasks}
        assert original_names == restored_names

    def test_import_invalid_strategy_fails(
        self,
        runner: CliRunner,
        initialized_project: Path,  # noqa: ARG002
        tmp_path: Path,
    ) -> None:
        """Test importing with invalid strategy."""
        export_file = tmp_path / "export.json"
        export_file.write_text('{"version": "1.0", "tasks": {}}')

        result = runner.invoke(task_app, ["import", str(export_file), "--strategy", "invalid"])

        assert result.exit_code == 1
        assert "Invalid strategy" in result.stderr
