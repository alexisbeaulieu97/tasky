"""Unit tests for project registry domain models."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from tasky_projects.models import ProjectMetadata, ProjectRegistry


class TestProjectMetadata:
    """Tests for ProjectMetadata model."""

    def test_create_with_valid_data(self) -> None:
        """Test creating ProjectMetadata with valid data."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
        )
        assert project.name == "my-project"
        assert project.path == Path("/home/user/projects/my-project")
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.last_accessed, datetime)
        assert project.tags == []

    def test_create_with_relative_path(self) -> None:
        """Test that relative paths are converted to absolute."""
        project = ProjectMetadata(
            name="test",
            path=Path("./test"),
        )
        assert project.path.is_absolute()

    def test_create_with_tags(self) -> None:
        """Test creating ProjectMetadata with tags."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
            tags=["work", "python"],
        )
        assert project.tags == ["work", "python"]

    def test_name_validation_empty(self) -> None:
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            ProjectMetadata(
                name="",
                path=Path("/home/user/projects/test"),
            )

    def test_name_validation_whitespace_only(self) -> None:
        """Test that whitespace-only names are rejected."""
        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            ProjectMetadata(
                name="   ",
                path=Path("/home/user/projects/test"),
            )

    def test_name_validation_invalid_characters(self) -> None:
        """Test that names with invalid characters are rejected."""
        with pytest.raises(ValidationError, match="Invalid project name"):
            ProjectMetadata(
                name="my/project",
                path=Path("/home/user/projects/test"),
            )

    def test_name_validation_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from names."""
        project = ProjectMetadata(
            name="  my-project  ",
            path=Path("/home/user/projects/test"),
        )
        assert project.name == "my-project"

    def test_name_validation_allows_valid_characters(self) -> None:
        """Test that valid characters are allowed in names."""
        valid_names = [
            "my-project",
            "my_project",
            "my project",
            "MyProject123",
            "project-123_test",
        ]
        for name in valid_names:
            project = ProjectMetadata(
                name=name,
                path=Path("/home/user/projects/test"),
            )
            assert project.name == name

    def test_json_serialization(self) -> None:
        """Test JSON serialization round-trip."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
            tags=["work"],
        )
        # Serialize to JSON
        json_data = project.model_dump(mode="json")
        # Deserialize back
        restored = ProjectMetadata.model_validate(json_data)
        assert restored.name == project.name
        assert restored.path == project.path
        assert restored.tags == project.tags
        assert restored.created_at == project.created_at
        assert restored.last_accessed == project.last_accessed


class TestProjectRegistry:
    """Tests for ProjectRegistry model."""

    def test_create_empty_registry(self) -> None:
        """Test creating an empty registry."""
        registry = ProjectRegistry()
        assert registry.projects == []
        assert registry.registry_version == "1.0"

    def test_get_by_name(self) -> None:
        """Test getting project by name."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
        )
        registry = ProjectRegistry(projects=[project])

        result = registry.get_by_name("my-project")
        assert result == project

        result = registry.get_by_name("nonexistent")
        assert result is None

    def test_get_by_path(self) -> None:
        """Test getting project by path."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
        )
        registry = ProjectRegistry(projects=[project])

        result = registry.get_by_path(Path("/home/user/projects/my-project"))
        assert result == project

        result = registry.get_by_path(Path("/home/user/other"))
        assert result is None

    def test_get_by_path_normalizes_paths(self) -> None:
        """Test that get_by_path handles path normalization."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project").resolve(),
        )
        registry = ProjectRegistry(projects=[project])

        # Test with relative path components
        result = registry.get_by_path(Path("/home/user/projects/../projects/my-project"))
        assert result == project

    def test_add_new_project(self) -> None:
        """Test adding a new project."""
        registry = ProjectRegistry()
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
        )

        is_new = registry.add_or_update(project)
        assert is_new is True
        assert len(registry.projects) == 1
        assert registry.projects[0] == project

    def test_update_existing_project(self) -> None:
        """Test updating an existing project."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
            tags=["old"],
        )
        registry = ProjectRegistry(projects=[project])

        updated = ProjectMetadata(
            name="renamed-project",
            path=Path("/home/user/projects/my-project"),
            tags=["new"],
        )

        is_new = registry.add_or_update(updated)
        assert is_new is False
        assert len(registry.projects) == 1
        assert registry.projects[0].name == "renamed-project"
        assert registry.projects[0].tags == ["new"]

    def test_remove_existing_project(self) -> None:
        """Test removing an existing project."""
        project = ProjectMetadata(
            name="my-project",
            path=Path("/home/user/projects/my-project"),
        )
        registry = ProjectRegistry(projects=[project])

        removed = registry.remove(Path("/home/user/projects/my-project"))
        assert removed is True
        assert len(registry.projects) == 0

    def test_remove_nonexistent_project(self) -> None:
        """Test removing a project that doesn't exist."""
        registry = ProjectRegistry()

        removed = registry.remove(Path("/home/user/projects/my-project"))
        assert removed is False
        assert len(registry.projects) == 0

    def test_json_serialization(self) -> None:
        """Test JSON serialization round-trip for registry."""
        project1 = ProjectMetadata(
            name="project1",
            path=Path("/home/user/projects/project1"),
        )
        project2 = ProjectMetadata(
            name="project2",
            path=Path("/home/user/projects/project2"),
            tags=["work"],
        )
        registry = ProjectRegistry(projects=[project1, project2])

        # Serialize to JSON
        json_data = registry.model_dump(mode="json")
        # Deserialize back
        restored = ProjectRegistry.model_validate(json_data)

        assert len(restored.projects) == 2
        assert restored.projects[0].name == "project1"
        assert restored.projects[1].name == "project2"
        assert restored.projects[1].tags == ["work"]
        assert restored.registry_version == "1.0"
        # Verify datetime fields are preserved
        assert restored.projects[0].created_at == project1.created_at
        assert restored.projects[0].last_accessed == project1.last_accessed
        assert restored.projects[1].created_at == project2.created_at
        assert restored.projects[1].last_accessed == project2.last_accessed
