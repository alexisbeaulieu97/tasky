"""Tests for advanced task filtering in the Tasky CLI."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tasky_cli.commands.projects import project_app
from tasky_cli.commands.tasks import task_app
from tasky_settings import create_task_service
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def project_with_dated_tasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary project with tasks from different dates."""
    project_dir = tmp_path / "test_project_dates"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Create the project
    service = create_task_service()

    # Create tasks with different dates
    base_date = datetime(2025, 11, 1, 0, 0, 0, tzinfo=UTC)

    # Task from November 1
    task1 = service.create_task("Old Task", "Created in early November")
    task1.created_at = base_date
    task1.updated_at = base_date
    service.update_task(task1)

    # Task from November 10
    task2 = service.create_task("Mid Task", "Created in mid November")
    task2.created_at = base_date + timedelta(days=9)
    task2.updated_at = base_date + timedelta(days=9)
    service.update_task(task2)

    # Task from November 20
    task3 = service.create_task("Recent Task", "Created in late November")
    task3.created_at = base_date + timedelta(days=19)
    task3.updated_at = base_date + timedelta(days=19)
    service.update_task(task3)

    return project_dir


@pytest.fixture
def project_with_searchable_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Create a temporary project with tasks containing various search terms."""
    project_dir = tmp_path / "test_project_search"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Create the project
    service = create_task_service()

    # Create tasks with different content
    service.create_task("Fix authentication bug", "Users cannot log in with special characters")
    service.create_task("Update documentation", "Add API examples to README")
    service.create_task("Implement authentication feature", "Add OAuth2 support")
    service.create_task("Buy groceries", "Get milk, eggs, and bread")

    return project_dir


class TestAdvancedDateFiltering:
    """Test date range filtering in CLI."""

    def test_filter_by_created_after(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering tasks created after a specific date."""
        result = runner.invoke(task_app, ["list", "--created-after", "2025-11-10"])

        assert result.exit_code == 0
        assert "Mid Task" in result.stdout
        assert "Recent Task" in result.stdout
        assert "Old Task" not in result.stdout

    def test_filter_by_created_before(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering tasks created before a specific date."""
        result = runner.invoke(task_app, ["list", "--created-before", "2025-11-10"])

        assert result.exit_code == 0
        assert "Old Task" in result.stdout
        assert "Mid Task" not in result.stdout
        assert "Recent Task" not in result.stdout

    def test_filter_by_date_range(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test filtering tasks within a specific date range."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--created-after",
                "2025-11-05",
                "--created-before",
                "2025-11-15",
            ],
        )

        assert result.exit_code == 0
        assert "Mid Task" in result.stdout
        assert "Old Task" not in result.stdout
        assert "Recent Task" not in result.stdout

    def test_filter_invalid_date_format(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test that invalid date formats show helpful error messages."""
        result = runner.invoke(task_app, ["list", "--created-after", "Jan 1"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid date format" in output
        assert "ISO 8601" in output
        assert "YYYY-MM-DD" in output

    def test_filter_invalid_created_before_format(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test that invalid created-before date shows error."""
        result = runner.invoke(task_app, ["list", "--created-before", "2025/11/01"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Invalid date format" in output

    def test_filter_date_with_no_matches(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test date filtering with no matching tasks."""
        result = runner.invoke(task_app, ["list", "--created-after", "2025-12-01"])

        assert result.exit_code == 0
        assert "No tasks match the specified filters" in result.stdout


class TestTextSearchFiltering:
    """Test text search filtering in CLI."""

    def test_search_by_name(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test searching tasks by name."""
        result = runner.invoke(task_app, ["list", "--search", "authentication"])

        assert result.exit_code == 0
        assert "Fix authentication bug" in result.stdout
        assert "Implement authentication feature" in result.stdout
        assert "Update documentation" not in result.stdout
        assert "Buy groceries" not in result.stdout

    def test_search_by_details(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test searching tasks by details."""
        result = runner.invoke(task_app, ["list", "--search", "OAuth2"])

        assert result.exit_code == 0
        assert "Implement authentication feature" in result.stdout
        assert "Fix authentication bug" not in result.stdout

    def test_search_case_insensitive(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test that search is case-insensitive."""
        result_lower = runner.invoke(task_app, ["list", "--search", "authentication"])
        result_upper = runner.invoke(task_app, ["list", "--search", "AUTHENTICATION"])
        result_mixed = runner.invoke(task_app, ["list", "--search", "AuThEnTiCaTiOn"])

        assert result_lower.exit_code == 0
        assert result_upper.exit_code == 0
        assert result_mixed.exit_code == 0

        # All should return the same results
        assert "Fix authentication bug" in result_lower.stdout
        assert "Fix authentication bug" in result_upper.stdout
        assert "Fix authentication bug" in result_mixed.stdout

    def test_search_partial_match(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test that search matches partial words."""
        result = runner.invoke(task_app, ["list", "--search", "auth"])

        assert result.exit_code == 0
        assert "Fix authentication bug" in result.stdout
        assert "Implement authentication feature" in result.stdout

    def test_search_with_no_matches(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test search with no matching tasks."""
        result = runner.invoke(task_app, ["list", "--search", "nonexistent"])

        assert result.exit_code == 0
        assert "No tasks match the specified filters" in result.stdout


class TestCombinedFiltering:
    """Test combining multiple filter criteria."""

    def test_status_and_date_filters(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test combining status and date filters."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--status",
                "pending",
                "--created-after",
                "2025-11-10",
            ],
        )

        assert result.exit_code == 0
        # All tasks are pending by default, so should see mid and recent tasks
        assert "Mid Task" in result.stdout or "Recent Task" in result.stdout

    def test_status_and_search_filters(
        self,
        runner: CliRunner,
        project_with_searchable_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test combining status and search filters."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--status",
                "pending",
                "--search",
                "authentication",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Fix authentication bug" in result.stdout
            or "Implement authentication feature" in result.stdout
        )

    def test_date_and_search_filters(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test combining date and search filters."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--created-after",
                "2025-11-10",
                "--search",
                "Recent",
            ],
        )

        assert result.exit_code == 0
        assert "Recent Task" in result.stdout
        assert "Mid Task" not in result.stdout

    def test_all_filters_combined(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test combining all filter types."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--status",
                "pending",
                "--created-after",
                "2025-11-01",
                "--created-before",
                "2025-11-15",
                "--search",
                "Mid",
            ],
        )

        assert result.exit_code == 0
        assert "Mid Task" in result.stdout
        assert "Old Task" not in result.stdout
        assert "Recent Task" not in result.stdout

    def test_combined_filters_no_matches(
        self,
        runner: CliRunner,
        project_with_dated_tasks: Path,  # noqa: ARG002
    ) -> None:
        """Test combined filters with no matching tasks."""
        result = runner.invoke(
            task_app,
            [
                "list",
                "--status",
                "completed",
                "--created-after",
                "2025-11-10",
            ],
        )

        assert result.exit_code == 0
        assert "No tasks match the specified filters" in result.stdout


class TestFilteringHelpText:
    """Test that help text documents the new filtering options."""

    def test_help_shows_date_options(self, runner: CliRunner) -> None:
        """Test that help text documents date filtering options."""
        result = runner.invoke(task_app, ["list", "--help"])

        assert result.exit_code == 0
        assert "--created-after" in result.stdout
        assert "--created-before" in result.stdout
        assert "ISO 8601" in result.stdout or "YYYY-MM-DD" in result.stdout

    def test_help_shows_search_option(self, runner: CliRunner) -> None:
        """Test that help text documents search option."""
        result = runner.invoke(task_app, ["list", "--help"])

        assert result.exit_code == 0
        assert "--search" in result.stdout
        assert "case-insensitive" in result.stdout or "name or details" in result.stdout
