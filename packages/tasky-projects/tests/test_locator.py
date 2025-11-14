"""Unit tests for project locator functionality."""

import json
from pathlib import Path

import pytest
from tasky_projects import ProjectConfig, StorageConfig
from tasky_projects.locator import (
    ProjectLocation,
    _check_directory_for_project,
    find_projects_recursive,
    find_projects_upward,
)


@pytest.fixture
def temp_project_tree(tmp_path: Path) -> Path:
    """Create a temporary directory tree with multiple tasky projects.

    Structure:
        tmp_path/
            .tasky/config.toml (backend: json)
            project1/
                .tasky/config.toml (backend: sqlite)
            project2/
                .tasky/config.toml (backend: json)
                subproject/
                    .tasky/config.toml (backend: sqlite)

    """
    # Root project
    root_config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    root_config.to_file(tmp_path / ".tasky" / "config.toml")

    # Project 1
    project1 = tmp_path / "project1"
    project1_config = ProjectConfig(storage=StorageConfig(backend="sqlite", path="tasks.db"))
    project1_config.to_file(project1 / ".tasky" / "config.toml")

    # Project 2
    project2 = tmp_path / "project2"
    project2_config = ProjectConfig(storage=StorageConfig(backend="json", path="data.json"))
    project2_config.to_file(project2 / ".tasky" / "config.toml")

    # Nested subproject
    subproject = project2 / "subproject"
    subproject_config = ProjectConfig(
        storage=StorageConfig(backend="sqlite", path="nested.db"),
    )
    subproject_config.to_file(subproject / ".tasky" / "config.toml")

    return tmp_path


def test_check_directory_for_project_with_valid_project(tmp_path: Path) -> None:
    """Test that _check_directory_for_project finds a valid project."""
    config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    config.to_file(tmp_path / ".tasky" / "config.toml")

    result = _check_directory_for_project(tmp_path)

    assert result is not None
    assert result.path == tmp_path
    assert result.backend == "json"
    assert result.storage_path == "tasks.json"


def test_check_directory_for_project_without_project(tmp_path: Path) -> None:
    """Test that _check_directory_for_project returns None for non-project directory."""
    result = _check_directory_for_project(tmp_path)
    assert result is None


def test_check_directory_for_project_with_invalid_config(tmp_path: Path) -> None:
    """Test that _check_directory_for_project handles invalid config gracefully."""
    # Create invalid config file
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    config_file = config_dir / "config.toml"
    config_file.write_text("invalid toml content [[[")

    result = _check_directory_for_project(tmp_path)
    assert result is None


def test_project_location_sorting() -> None:
    """Test that ProjectLocation objects can be sorted by path."""
    loc1 = ProjectLocation(path=Path("/a/b"), backend="json", storage_path="tasks.json")
    loc2 = ProjectLocation(path=Path("/a/a"), backend="json", storage_path="tasks.json")
    loc3 = ProjectLocation(path=Path("/b"), backend="json", storage_path="tasks.json")

    sorted_locs = sorted([loc1, loc2, loc3])

    assert sorted_locs[0].path == Path("/a/a")
    assert sorted_locs[1].path == Path("/a/b")
    assert sorted_locs[2].path == Path("/b")


def test_find_projects_upward_single_project(tmp_path: Path) -> None:
    """Test finding a single project when searching upward."""
    config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    config.to_file(tmp_path / ".tasky" / "config.toml")

    # Search from a subdirectory
    subdir = tmp_path / "subdir" / "nested"
    subdir.mkdir(parents=True)

    projects = find_projects_upward(subdir)

    assert len(projects) == 1
    assert projects[0].path == tmp_path
    assert projects[0].backend == "json"


def test_find_projects_upward_multiple_projects(tmp_path: Path) -> None:
    """Test finding multiple projects when searching upward."""
    # Create nested projects
    config1 = ProjectConfig(storage=StorageConfig(backend="json", path="root.json"))
    config1.to_file(tmp_path / ".tasky" / "config.toml")

    nested = tmp_path / "nested"
    config2 = ProjectConfig(storage=StorageConfig(backend="sqlite", path="nested.db"))
    config2.to_file(nested / ".tasky" / "config.toml")

    deeper = nested / "deeper"
    deeper.mkdir(parents=True)

    projects = find_projects_upward(deeper)

    assert len(projects) == 2
    # Results should be sorted by path
    assert projects[0].path == tmp_path
    assert projects[0].backend == "json"
    assert projects[1].path == nested
    assert projects[1].backend == "sqlite"


def test_find_projects_upward_no_projects(tmp_path: Path) -> None:
    """Test that find_projects_upward returns empty list when no projects found."""
    projects = find_projects_upward(tmp_path)
    assert projects == []


def test_find_projects_upward_stops_at_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that find_projects_upward stops at home directory."""
    # Mock Path.home() to return tmp_path as home
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Create a project at "home"
    config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    config.to_file(tmp_path / ".tasky" / "config.toml")

    # Search from a subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    projects = find_projects_upward(subdir)

    # Should find the home project but not go beyond
    assert len(projects) == 1
    assert projects[0].path == tmp_path


def test_find_projects_recursive_single_level(tmp_path: Path) -> None:
    """Test finding projects recursively at single level."""
    # Create two projects side by side
    project1 = tmp_path / "project1"
    config1 = ProjectConfig(storage=StorageConfig(backend="json", path="tasks1.json"))
    config1.to_file(project1 / ".tasky" / "config.toml")

    project2 = tmp_path / "project2"
    config2 = ProjectConfig(storage=StorageConfig(backend="sqlite", path="tasks2.db"))
    config2.to_file(project2 / ".tasky" / "config.toml")

    projects = find_projects_recursive(tmp_path)

    assert len(projects) == 2
    assert projects[0].path == project1
    assert projects[0].backend == "json"
    assert projects[1].path == project2
    assert projects[1].backend == "sqlite"


def test_find_projects_recursive_nested(temp_project_tree: Path) -> None:
    """Test finding projects recursively with nested structure."""
    projects = find_projects_recursive(temp_project_tree)

    assert len(projects) == 4
    # Should find root, project1, project2, and subproject
    paths = [p.path for p in projects]
    assert temp_project_tree in paths
    assert temp_project_tree / "project1" in paths
    assert temp_project_tree / "project2" in paths
    assert temp_project_tree / "project2" / "subproject" in paths


def test_find_projects_recursive_no_projects(tmp_path: Path) -> None:
    """Test that find_projects_recursive returns empty list when no projects found."""
    projects = find_projects_recursive(tmp_path)
    assert projects == []


def test_find_projects_recursive_from_current_directory(
    temp_project_tree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test find_projects_recursive with default current directory."""
    # Change to temp directory
    monkeypatch.chdir(temp_project_tree)

    projects = find_projects_recursive()

    assert len(projects) == 4


def test_find_projects_upward_from_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test find_projects_upward with default current directory."""
    config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    config.to_file(tmp_path / ".tasky" / "config.toml")

    monkeypatch.chdir(tmp_path)

    projects = find_projects_upward()

    assert len(projects) == 1
    assert projects[0].path == tmp_path


def test_find_projects_recursive_skips_tasky_directories(tmp_path: Path) -> None:
    """Test that recursive search doesn't descend into .tasky directories."""
    # Create a project
    config = ProjectConfig(storage=StorageConfig(backend="json", path="tasks.json"))
    config.to_file(tmp_path / ".tasky" / "config.toml")

    # Create a nested directory inside .tasky (should be ignored)
    nested = tmp_path / ".tasky" / "nested"
    nested.mkdir()
    config2 = ProjectConfig(storage=StorageConfig(backend="sqlite", path="should_not_find.db"))
    config2.to_file(nested / ".tasky" / "config.toml")

    projects = find_projects_recursive(tmp_path)

    # Should only find the root project, not the nested one inside .tasky
    assert len(projects) == 1
    assert projects[0].path == tmp_path


def test_find_projects_with_legacy_json_config(tmp_path: Path) -> None:
    """Test that locator can find projects with legacy config.json files."""
    # Create a legacy JSON config
    config_dir = tmp_path / ".tasky"
    config_dir.mkdir()
    config_file = config_dir / "config.json"

    config_data = {
        "version": "1.0",
        "storage": {"backend": "json", "path": "legacy.json"},
        "created_at": "2025-11-14T12:00:00Z",
    }
    config_file.write_text(json.dumps(config_data))

    projects = find_projects_recursive(tmp_path)

    assert len(projects) == 1
    assert projects[0].path == tmp_path
    assert projects[0].backend == "json"
    assert projects[0].storage_path == "legacy.json"


def test_find_projects_sorted_by_path(temp_project_tree: Path) -> None:
    """Test that results are consistently sorted by path."""
    projects = find_projects_recursive(temp_project_tree)

    # Verify sorting
    for i in range(len(projects) - 1):
        assert str(projects[i].path) < str(projects[i + 1].path)
