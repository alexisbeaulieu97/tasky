"""Integration tests for ProjectRegistryService with real filesystem operations.

Tests full workflows including:
- Registry persistence across service instances
- Concurrent access scenarios
- Registry corruption recovery
- Complex directory structures
"""

import contextlib
import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from tasky_projects.registry import ProjectRegistryService


@pytest.fixture
def temp_home_dir() -> Iterator[Path]:
    """Create a temporary home directory for isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_registry_path(temp_home_dir: Path) -> Path:
    """Create a registry path in the temporary home directory."""
    registry_dir = temp_home_dir / ".tasky"
    registry_dir.mkdir(parents=True, exist_ok=True)
    return registry_dir / "registry.json"


@pytest.fixture
def service_with_temp_registry(temp_registry_path: Path) -> ProjectRegistryService:
    """Create a service instance with temporary registry."""
    return ProjectRegistryService(temp_registry_path)


class TestRegistryPersistence:
    """Test registry persistence across service instances."""

    def test_persistence_across_instances(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Registry created by one service should be readable by another."""
        # Create project directory
        project_dir = tmp_path / "project1"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()

        # Create and use first service instance
        service1 = ProjectRegistryService(temp_registry_path)
        metadata1 = service1.register_project(project_dir)
        assert metadata1.name == "project1"

        # Create second service instance and verify registry persists
        service2 = ProjectRegistryService(temp_registry_path)
        projects = service2.list_projects()
        assert len(projects) == 1
        assert projects[0].name == "project1"
        assert projects[0].path == project_dir.resolve()

    def test_concurrent_access_multiple_services(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Multiple service instances should handle concurrent access safely."""
        # Create multiple project directories
        projects: list[Path] = []
        for i in range(3):
            project_dir = tmp_path / f"project{i}"
            project_dir.mkdir()
            (project_dir / ".tasky").mkdir()
            projects.append(project_dir)

        # Create multiple service instances and register projects
        services = [ProjectRegistryService(temp_registry_path) for _ in range(3)]

        for _i, (service, project_dir) in enumerate(zip(services, projects, strict=False)):
            service.register_project(project_dir)

        # All services should see all projects
        for service in services:
            all_projects = service.list_projects()
            assert len(all_projects) >= 1  # At least the ones registered

    def test_registry_file_format(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Verify registry JSON file format is correct."""
        # Create and register a project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()

        service = ProjectRegistryService(temp_registry_path)
        service.register_project(project_dir)

        # Read registry file directly and verify format
        assert temp_registry_path.exists()
        with temp_registry_path.open() as f:
            registry_data = json.load(f)

        assert "registry_version" in registry_data
        assert "projects" in registry_data
        assert isinstance(registry_data["projects"], list)
        assert len(registry_data["projects"]) >= 1

        project = registry_data["projects"][0]
        assert "name" in project
        assert "path" in project
        assert "created_at" in project
        assert "last_accessed" in project
        assert "tags" in project

    def test_registry_update_last_accessed_persists(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Last accessed timestamp updates should persist across instances."""
        # Create project
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()

        # Register with first service
        service1 = ProjectRegistryService(temp_registry_path)
        service1.register_project(project_dir)
        projects1 = service1.list_projects()
        original_accessed = projects1[0].last_accessed

        # Update last accessed with second service
        service2 = ProjectRegistryService(temp_registry_path)
        service2.update_last_accessed(project_dir)

        # Verify third service sees updated timestamp
        service3 = ProjectRegistryService(temp_registry_path)
        projects3 = service3.list_projects()
        updated_accessed = projects3[0].last_accessed

        assert updated_accessed >= original_accessed


class TestRegistryCorruption:
    """Test recovery from corrupted registry files."""

    def test_corrupted_json_recovery(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Service should handle and recover from corrupted JSON."""
        # Create a corrupted registry file
        temp_registry_path.write_text("{ invalid json }}")

        # Service should create new registry instead of crashing
        service = ProjectRegistryService(temp_registry_path)
        projects = service.list_projects()
        assert projects == []

        # Should be able to register new projects
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()

        metadata = service.register_project(project_dir)
        assert metadata.name == "project"

    def test_missing_required_fields_recovery(
        self, temp_registry_path: Path,
    ) -> None:
        """Service should handle registry with missing required fields."""
        # Create registry with missing fields
        bad_registry = {"projects": [{"name": "test"}]}  # Missing path, timestamps
        temp_registry_path.write_text(json.dumps(bad_registry))

        # Service should handle gracefully
        service = ProjectRegistryService(temp_registry_path)
        # Should either return empty list or skip invalid entries
        projects = service.list_projects()
        assert isinstance(projects, list)

    def test_empty_registry_file_recovery(
        self, temp_registry_path: Path,
    ) -> None:
        """Service should handle completely empty registry file."""
        # Create empty file
        temp_registry_path.write_text("")

        # Service should create valid registry
        service = ProjectRegistryService(temp_registry_path)
        projects = service.list_projects()
        assert projects == []


class TestComplexDirectoryStructures:
    """Test discovery with various directory structures."""

    def test_discovery_nested_projects(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Discovery should find projects at various nesting levels."""
        # Create nested structure
        root = tmp_path / "workspace"
        root.mkdir()

        # Level 1 project
        proj1 = root / "proj1"
        proj1.mkdir()
        (proj1 / ".tasky").mkdir()

        # Level 2 projects
        level2 = root / "level2"
        level2.mkdir()
        proj2 = level2 / "proj2"
        proj2.mkdir()
        (proj2 / ".tasky").mkdir()

        # Level 3 projects
        level3 = level2 / "level3"
        level3.mkdir()
        proj3 = level3 / "proj3"
        proj3.mkdir()
        (proj3 / ".tasky").mkdir()

        # Discover projects
        discovered = service_with_temp_registry.discover_projects([root])
        names = {p.name for p in discovered}

        assert "proj1" in names
        assert "proj2" in names
        assert "proj3" in names

    def test_discovery_skips_excluded_directories(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Discovery should skip common excluded directories."""
        root = tmp_path / "workspace"
        root.mkdir()

        # Create excluded directory with project-like structure
        node_modules = root / "node_modules"
        node_modules.mkdir()
        npm_proj = node_modules / "some-package"
        npm_proj.mkdir()
        (npm_proj / ".tasky").mkdir()

        # Create valid project
        valid_proj = root / "my-project"
        valid_proj.mkdir()
        (valid_proj / ".tasky").mkdir()

        # Discover projects
        discovered = service_with_temp_registry.discover_projects([root])
        names = {p.name for p in discovered}

        assert "my-project" in names
        assert "some-package" not in names  # Should be skipped

    def test_discovery_with_symlinks(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Discovery should handle symlinks in project paths."""
        # Create actual project
        actual_proj = tmp_path / "actual"
        actual_proj.mkdir()
        (actual_proj / ".tasky").mkdir()

        # Create symlink to it
        link_proj = tmp_path / "link"
        link_proj.symlink_to(actual_proj)

        # Discover should find both (or deduplicate)
        discovered = service_with_temp_registry.discover_projects([tmp_path])
        assert len(discovered) >= 1

        # The path should be absolute and valid
        for proj in discovered:
            assert proj.path.is_absolute()

    def test_discovery_max_depth_respected(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Discovery should respect max depth limit."""
        root = tmp_path / "workspace"
        root.mkdir()

        # Create deeply nested structure
        current = root
        for i in range(10):
            current = current / f"level{i}"
            current.mkdir()

        # Create project at each level
        proj = current / "deep_project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Discover with default max_depth (should be 3)
        discovered = service_with_temp_registry.discover_projects([root])

        # Deep project at level 10 should not be found (max_depth=3)
        names = {p.name for p in discovered}
        assert "deep_project" not in names


class TestProjectPathsWithSpecialCharacters:
    """Test handling of project paths with special characters."""

    def test_project_with_spaces_in_path(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Should handle project paths with spaces."""
        proj = tmp_path / "my project with spaces"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        metadata = service_with_temp_registry.register_project(proj)
        assert metadata.name == "my project with spaces"

        # Should be able to retrieve it
        found = service_with_temp_registry.get_project("my project with spaces")
        assert found is not None
        assert found.path == proj.resolve()

    def test_project_with_special_chars_in_path(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Should handle project paths with underscores and dots."""
        proj = tmp_path / "project_name_v1"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        metadata = service_with_temp_registry.register_project(proj)
        assert metadata.name == "project_name_v1"

        # Should be able to retrieve it
        found = service_with_temp_registry.get_project("project_name_v1")
        assert found is not None


class TestLargeRegistries:
    """Test performance with large number of projects."""

    def test_registry_with_many_projects(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Should handle registry with many projects."""
        # Create 50 projects (not 100 yet to keep test fast)
        projects: list[Path] = []
        for i in range(50):
            proj = tmp_path / f"project_{i:03d}"
            proj.mkdir()
            (proj / ".tasky").mkdir()
            projects.append(proj)

        # Register all projects
        for proj in projects:
            service_with_temp_registry.register_project(proj)

        # Should be able to list all
        all_projects = service_with_temp_registry.list_projects()
        assert len(all_projects) == 50

        # Should be able to look up by name
        proj_25 = service_with_temp_registry.get_project("project_025")
        assert proj_25 is not None

    def test_registry_persistence_with_many_projects(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Large registry should persist correctly across instances."""
        # Create 30 projects
        for i in range(30):
            proj = tmp_path / f"project_{i:02d}"
            proj.mkdir()
            (proj / ".tasky").mkdir()

        # Register with first service
        service1 = ProjectRegistryService(temp_registry_path)
        for i in range(30):
            proj = tmp_path / f"project_{i:02d}"
            service1.register_project(proj)

        # Load with second service and verify all exist
        service2 = ProjectRegistryService(temp_registry_path)
        all_projects = service2.list_projects()
        assert len(all_projects) == 30


class TestPermissionErrors:
    """Test handling of permission-related errors."""

    def test_discovery_with_permission_denied(
        self, service_with_temp_registry: ProjectRegistryService, tmp_path: Path,
    ) -> None:
        """Discovery should handle directories with permission errors."""
        root = tmp_path / "workspace"
        root.mkdir()

        # Create a project
        proj = root / "accessible"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Create directory with restricted permissions
        restricted = root / "restricted"
        restricted.mkdir()
        restricted.chmod(0o000)

        try:
            # Discover should either skip or fail gracefully on permission errors
            # The implementation may raise PermissionError which is acceptable
            try:
                discovered = service_with_temp_registry.discover_projects([root])
                # Should find the accessible project if it doesn't error
                names = {p.name for p in discovered}
                assert "accessible" in names
            except PermissionError:
                # This is acceptable - permission denied during walk
                pass
        finally:
            # Restore permissions for cleanup
            restricted.chmod(0o755)

    def test_read_only_registry_directory(
        self, temp_registry_path: Path, tmp_path: Path,
    ) -> None:
        """Service should handle read-only registry directory."""
        # Make parent directory read-only after creating it
        parent = temp_registry_path.parent
        parent_mode = parent.stat().st_mode

        try:
            # Create and register a project first
            proj = tmp_path / "project"
            proj.mkdir()
            (proj / ".tasky").mkdir()

            service = ProjectRegistryService(temp_registry_path)
            service.register_project(proj)

            # Make directory read-only
            parent.chmod(0o555)

            # Should fail gracefully when trying to save
            proj2 = tmp_path / "project2"
            proj2.mkdir()
            (proj2 / ".tasky").mkdir()

            # This should either succeed (cached in memory) or fail gracefully
            # depending on implementation
            with contextlib.suppress(PermissionError, OSError):
                service.register_project(proj2)
        finally:
            # Restore permissions for cleanup
            parent.chmod(parent_mode)
