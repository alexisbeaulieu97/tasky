"""Tests for project list command."""

from pathlib import Path

import pytest
from tasky_cli.commands.projects import project_app
from typer.testing import CliRunner


@pytest.fixture
def empty_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an empty directory and change to it."""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    return empty


@pytest.fixture
def single_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a directory with a single initialized project."""
    project_path = tmp_path / "single_project"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    return project_path


@pytest.fixture
def nested_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a directory tree with multiple nested projects.

    Structure:
        tmp_path/
            root_project/
                .tasky/ (json backend)
                subproject1/
                    .tasky/ (sqlite backend)
                subproject2/
                    .tasky/ (json backend)
                    nested/
                        .tasky/ (sqlite backend)

    """
    root = tmp_path / "root_project"
    root.mkdir()
    runner = CliRunner()

    # Initialize root project
    monkeypatch.chdir(root)
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Initialize subproject1 with sqlite
    subproject1 = root / "subproject1"
    subproject1.mkdir()
    monkeypatch.chdir(subproject1)
    result = runner.invoke(project_app, ["init", "--backend", "sqlite"])
    assert result.exit_code == 0

    # Initialize subproject2
    subproject2 = root / "subproject2"
    subproject2.mkdir()
    monkeypatch.chdir(subproject2)
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    # Initialize nested project with sqlite
    nested = subproject2 / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    result = runner.invoke(project_app, ["init", "--backend", "sqlite"])
    assert result.exit_code == 0

    # Return to root for tests
    monkeypatch.chdir(root)
    return root


class TestProjectListCommand:
    """Test suite for project list command."""

    def test_list_no_projects_found(
        self,
        runner: CliRunner,
        empty_dir: Path,  # noqa: ARG002
    ) -> None:
        """Test listing when no projects exist."""
        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        assert "No projects found." in result.stdout
        assert "Run 'tasky project init' to create one." in result.stdout

    def test_list_single_project(
        self,
        runner: CliRunner,
        single_project: Path,
    ) -> None:
        """Test listing a single project."""
        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        assert "Found 1 project:" in result.stdout
        assert str(single_project) in result.stdout
        assert "Backend: json" in result.stdout
        assert "Storage: tasks.json" in result.stdout

    def test_list_upward_from_nested_directory(
        self,
        runner: CliRunner,
        nested_projects: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test upward search finds parent projects."""
        # Change to deepest nested directory
        nested = nested_projects / "subproject2" / "nested"
        monkeypatch.chdir(nested)

        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        # Should find nested, subproject2, and root (3 projects total)
        assert "Found 3 project" in result.stdout
        assert str(nested_projects) in result.stdout
        assert str(nested_projects / "subproject2") in result.stdout
        assert str(nested) in result.stdout

    def test_list_recursive_finds_all_projects(
        self,
        runner: CliRunner,
        nested_projects: Path,
    ) -> None:
        """Test recursive search finds all nested projects."""
        result = runner.invoke(project_app, ["list", "--recursive"])

        assert result.exit_code == 0
        # Should find all 4 projects
        assert "Found 4 project" in result.stdout
        assert str(nested_projects) in result.stdout
        assert str(nested_projects / "subproject1") in result.stdout
        assert str(nested_projects / "subproject2") in result.stdout
        assert str(nested_projects / "subproject2" / "nested") in result.stdout

    def test_list_with_custom_root(
        self,
        runner: CliRunner,
        nested_projects: Path,
        empty_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test listing from a custom root directory."""
        # Change to empty directory
        monkeypatch.chdir(empty_dir)

        # List from nested_projects directory
        result = runner.invoke(
            project_app,
            ["list", "--root", str(nested_projects), "--recursive"],
        )

        assert result.exit_code == 0
        assert "Found 4 project" in result.stdout

    def test_list_recursive_short_flag(
        self,
        runner: CliRunner,
        nested_projects: Path,  # noqa: ARG002
    ) -> None:
        """Test recursive search with -r short flag."""
        result = runner.invoke(project_app, ["list", "-r"])

        assert result.exit_code == 0
        assert "Found 4 project" in result.stdout

    def test_list_displays_backend_types(
        self,
        runner: CliRunner,
        nested_projects: Path,  # noqa: ARG002
    ) -> None:
        """Test that different backend types are displayed correctly."""
        result = runner.invoke(project_app, ["list", "--recursive"])

        assert result.exit_code == 0
        # Check for both json and sqlite backends
        assert "Backend: json" in result.stdout
        assert "Backend: sqlite" in result.stdout

    def test_list_displays_storage_paths(
        self,
        runner: CliRunner,
        single_project: Path,  # noqa: ARG002
    ) -> None:
        """Test that storage paths are displayed."""
        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        assert "Storage: tasks.json" in result.stdout

    def test_list_output_format_consistency(
        self,
        runner: CliRunner,
        nested_projects: Path,  # noqa: ARG002
    ) -> None:
        """Test that output format is consistent across multiple projects."""
        result = runner.invoke(project_app, ["list", "--recursive"])

        assert result.exit_code == 0
        # Each project should have Path, Backend, and Storage fields
        path_count = result.stdout.count("Path:")
        backend_count = result.stdout.count("Backend:")
        storage_count = result.stdout.count("Storage:")

        assert path_count == 4
        assert backend_count == 4
        assert storage_count == 4

    def test_list_projects_sorted_by_path(
        self,
        runner: CliRunner,
        nested_projects: Path,
    ) -> None:
        """Test that projects are listed in sorted order."""
        result = runner.invoke(project_app, ["list", "--recursive"])

        assert result.exit_code == 0
        # Extract project paths from output
        lines = result.stdout.split("\n")
        paths = [line.strip() for line in lines if line.strip().startswith("Path:")]

        # Verify sorted order (should be alphabetical)
        assert len(paths) == 4
        # Root should come first, then subproject1, then subproject2, then nested
        assert str(nested_projects) in paths[0]
        assert "subproject1" in paths[1]
        assert "subproject2" in paths[2]
        assert "nested" in paths[3]

    def test_list_help_text(
        self,
        runner: CliRunner,
    ) -> None:
        """Test that help text is clear and informative."""
        result = runner.invoke(project_app, ["list", "--help"])

        assert result.exit_code == 0
        assert "List all tasky projects" in result.stdout
        assert "--recursive" in result.stdout
        assert "--root" in result.stdout
        assert "Search recursively" in result.stdout


class TestProjectListEdgeCases:
    """Test edge cases for project list command."""

    def test_list_with_nonexistent_root(
        self,
        runner: CliRunner,
    ) -> None:
        """Test listing with a non-existent root directory."""
        result = runner.invoke(
            project_app,
            ["list", "--root", "/nonexistent/path/to/nowhere"],
        )

        # Should handle gracefully (either error or no results)
        # Implementation may vary, but shouldn't crash
        assert result.exit_code in (0, 1)

    def test_list_upward_stops_at_boundary(
        self,
        runner: CliRunner,
        single_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that upward search stops at appropriate boundary."""
        # Create a deeply nested subdirectory
        deep = single_project / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        monkeypatch.chdir(deep)

        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        # Should find the single root project
        assert "Found 1 project:" in result.stdout

    def test_list_recursive_from_subproject(
        self,
        runner: CliRunner,
        nested_projects: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test recursive search from a subproject directory."""
        subproject2 = nested_projects / "subproject2"
        monkeypatch.chdir(subproject2)

        result = runner.invoke(project_app, ["list", "--recursive"])

        assert result.exit_code == 0
        # Should find subproject2 and nested (2 projects)
        assert "Found 2 project" in result.stdout
        assert str(subproject2) in result.stdout
        assert "nested" in result.stdout
        # Should NOT find root or subproject1
        assert "subproject1" not in result.stdout
