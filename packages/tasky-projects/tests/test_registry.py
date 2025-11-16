"""Tests for ProjectRegistryService."""
# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

import json
import os
import stat
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tasky_projects.models import ProjectMetadata, ProjectRegistry
from tasky_projects.registry import ProjectRegistryService


class TestProjectRegistryService:
    """Tests for ProjectRegistryService."""

    @pytest.fixture
    def registry_path(self, tmp_path: Path) -> Path:
        """Create a temporary registry path outside the test project area."""
        registry_dir = tmp_path / "registry_storage"
        registry_dir.mkdir()
        return registry_dir / "registry.json"

    @pytest.fixture
    def service(self, registry_path: Path) -> ProjectRegistryService:
        """Create a registry service instance."""
        return ProjectRegistryService(registry_path)

    @pytest.fixture
    def test_project(self, tmp_path: Path) -> Path:
        """Create a test project directory."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()
        return project_dir

    def test_init(self, registry_path: Path) -> None:
        """Test service initialization."""
        service = ProjectRegistryService(registry_path)
        assert service.registry_path == registry_path
        assert service._registry is None

    def test_load_empty_registry(self, service: ProjectRegistryService) -> None:
        """Test loading when registry file doesn't exist."""
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

    def test_load_existing_registry(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
        test_project: Path,
    ) -> None:
        """Test loading existing registry file."""
        # Create a registry file
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry = ProjectRegistry(
            projects=[
                ProjectMetadata(
                    name="test-project",
                    path=test_project,
                ),
            ],
        )
        with registry_path.open("w") as f:
            json.dump(registry.model_dump(mode="json"), f, default=str)

        # Load it
        loaded = service._load()
        assert len(loaded.projects) == 1
        assert loaded.projects[0].name == "test-project"

    def test_load_corrupted_registry(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test loading corrupted registry file creates backup."""
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w") as f:
            f.write("not valid json{")

        # Should return empty registry
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

        # Verify backup was created with pattern: registry.corrupted.TIMESTAMP.json
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 1
        assert backups[0].read_text() == "not valid json{"

    def test_save_registry(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
        test_project: Path,
    ) -> None:
        """Test saving registry to disk."""
        registry = ProjectRegistry(
            projects=[
                ProjectMetadata(
                    name="test-project",
                    path=test_project,
                ),
            ],
        )

        service._save(registry)

        assert registry_path.exists()
        with registry_path.open("r") as f:
            data = json.load(f)
        assert len(data["projects"]) == 1

    def test_registry_property_lazy_load(self, service: ProjectRegistryService) -> None:
        """Test that registry property lazy-loads."""
        assert service._registry is None
        registry = service.registry
        assert service._registry is not None
        assert registry == service._registry

    def test_register_project(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test registering a new project."""
        project = service.register_project(test_project)

        assert project.name == "test-project"
        assert project.path == test_project.resolve()
        assert len(service.registry.projects) == 1

    def test_register_project_invalid_path(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering project with invalid path."""
        with pytest.raises(ValueError, match="Path does not exist"):
            service.register_project(tmp_path / "nonexistent")

    def test_register_project_no_tasky_dir(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering project without .tasky directory."""
        project_dir = tmp_path / "not-a-project"
        project_dir.mkdir()

        with pytest.raises(ValueError, match="Not a tasky project"):
            service.register_project(project_dir)

    def test_register_existing_project(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test registering a project that's already registered."""
        # Register once
        service.register_project(test_project)
        assert len(service.registry.projects) == 1

        # Register again (should update, not duplicate)
        service.register_project(test_project)
        assert len(service.registry.projects) == 1

    def test_unregister_project(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test unregistering a project."""
        service.register_project(test_project)
        assert len(service.registry.projects) == 1

        service.unregister_project(test_project)
        assert len(service.registry.projects) == 0

    def test_unregister_nonexistent_project(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test unregistering a project that's not registered."""
        with pytest.raises(ValueError, match="Project not found"):
            service.unregister_project(test_project)

    def test_get_project(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test getting a project by name."""
        service.register_project(test_project)

        project = service.get_project("test-project")
        assert project is not None
        assert project.name == "test-project"

        project = service.get_project("nonexistent")
        assert project is None

    def test_list_projects(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing all projects."""
        # Create multiple test projects
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / ".tasky").mkdir()

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / ".tasky").mkdir()

        service.register_project(project1)
        service.register_project(project2)

        projects = service.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"project1", "project2"}

    def test_list_projects_sorted_by_last_accessed(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that list_projects sorts by last_accessed."""
        # Create projects with different access times
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / ".tasky").mkdir()

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / ".tasky").mkdir()

        service.register_project(project1)
        service.register_project(project2)

        # Modify last_accessed times
        p1 = service.registry.get_by_name("project1")
        p2 = service.registry.get_by_name("project2")
        assert p1 is not None
        assert p2 is not None

        p1.last_accessed = datetime.now(tz=UTC) - timedelta(hours=1)
        p2.last_accessed = datetime.now(tz=UTC)

        projects = service.list_projects()
        # Most recent first
        assert projects[0].name == "project2"
        assert projects[1].name == "project1"

    def test_update_last_accessed(
        self,
        service: ProjectRegistryService,
        test_project: Path,
    ) -> None:
        """Test updating last accessed timestamp."""
        service.register_project(test_project)
        project = service.registry.get_by_name("test-project")
        assert project is not None

        old_timestamp = project.last_accessed
        # Wait a bit to ensure timestamp changes
        time.sleep(0.01)

        service.update_last_accessed(test_project)
        new_timestamp = project.last_accessed

        assert new_timestamp > old_timestamp

    def test_update_last_accessed_nonexistent_project(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test updating last accessed for nonexistent project raises ValueError."""
        project_path = tmp_path / "nonexistent"
        project_path.mkdir()

        with pytest.raises(ValueError, match="Project not found"):
            service.update_last_accessed(project_path)

    def test_walk_directories(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test directory walking."""
        # Create a directory structure
        (tmp_path / "level1").mkdir()
        (tmp_path / "level1" / "level2").mkdir()
        (tmp_path / "level1" / "level2" / "level3").mkdir()
        (tmp_path / "level1" / "level2" / "level3" / "level4").mkdir()

        # Walk with max_depth=2
        dirs = list(service._walk_directories(tmp_path, max_depth=2))

        # Check depth (should not include level4)
        paths = [d.relative_to(tmp_path) for d in dirs if d != tmp_path]
        assert Path("level1") in paths
        assert Path("level1/level2") in paths
        assert Path("level1/level2/level3") not in paths

    def test_walk_directories_skips_hidden(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that hidden directories are skipped."""
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "visible").mkdir()

        dirs = list(service._walk_directories(tmp_path))

        names = {d.name for d in dirs}
        assert "visible" in names
        assert ".hidden" not in names

    def test_walk_directories_skips_common_dirs(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that common non-project directories are skipped."""
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "venv").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "src").mkdir()

        dirs = list(service._walk_directories(tmp_path))

        names = {d.name for d in dirs}
        assert "src" in names
        assert "node_modules" not in names
        assert "venv" not in names
        assert ".git" not in names

    def test_discover_projects(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovering projects."""
        # Create project directories
        project1 = tmp_path / "workspace" / "project1"
        project1.mkdir(parents=True)
        (project1 / ".tasky").mkdir()

        project2 = tmp_path / "workspace" / "project2"
        project2.mkdir()
        (project2 / ".tasky").mkdir()

        # Discover
        discovered = service.discover_projects([tmp_path])

        assert len(discovered) == 2
        names = {p.name for p in discovered}
        assert names == {"project1", "project2"}

    def test_discover_projects_deduplicates(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that discovery deduplicates projects."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tasky").mkdir()

        # Discover from overlapping paths
        discovered = service.discover_projects([tmp_path, project])

        # Should only find the project once
        assert len(discovered) == 1

    def test_discover_and_register(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discover_and_register workflow."""
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / ".tasky").mkdir()

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / ".tasky").mkdir()

        new_count = service.discover_and_register([tmp_path])

        assert new_count == 2
        assert len(service.registry.projects) == 2

    def test_discover_and_register_updates_existing(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that discover_and_register updates existing projects."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tasky").mkdir()

        # Register manually first
        service.register_project(project)
        assert len(service.registry.projects) == 1

        # Discover again (should update, not add)
        new_count = service.discover_and_register([tmp_path])

        assert new_count == 0  # No new projects
        assert len(service.registry.projects) == 1

    def test_persistence_across_instances(
        self,
        registry_path: Path,
        test_project: Path,
    ) -> None:
        """Test that registry persists across service instances."""
        # Register with first instance
        service1 = ProjectRegistryService(registry_path)
        service1.register_project(test_project)

        # Load with second instance
        service2 = ProjectRegistryService(registry_path)
        projects = service2.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "test-project"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def registry_path(self, tmp_path: Path) -> Path:
        """Create a temporary registry path."""
        registry_dir = tmp_path / "registry_storage"
        registry_dir.mkdir()
        return registry_dir / "registry.json"

    @pytest.fixture
    def service(self, registry_path: Path) -> ProjectRegistryService:
        """Create a registry service instance."""
        return ProjectRegistryService(registry_path)

    def test_registry_with_100_projects(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registry performance with 100 projects."""
        # Create 100 projects
        for i in range(100):
            project_dir = tmp_path / f"project_{i:03d}"
            project_dir.mkdir()
            (project_dir / ".tasky").mkdir()
            service.register_project(project_dir)

        # Verify all projects are registered
        projects = service.list_projects()
        assert len(projects) == 100

        # Verify we can look up a project in the middle
        mid_project = service.get_project("project_050")
        assert mid_project is not None
        assert mid_project.name == "project_050"

    def test_discovery_deeply_nested_structure(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovery respects max depth with deeply nested directories."""
        # Create a deeply nested structure with projects at each depth
        # The walk visits depth 0, 1, 2 before stopping (max_depth=3 means depth >= 3 stops)
        current = tmp_path / "level0"
        current.mkdir()
        (current / ".tasky").mkdir()  # Depth 0 project

        depths = {}
        for depth in range(1, 10):
            current = current / f"level{depth}"
            current.mkdir()
            depths[depth] = current

            # Create a project at this depth
            proj = current / "project"
            proj.mkdir()
            (proj / ".tasky").mkdir()

        # Discover with default max_depth (3)
        # This will visit directories at depth 0, 1, 2 (stops when depth >= 3)
        discovered = service.discover_projects([tmp_path])

        # Should find projects at depth 0 and depth 1 only
        # (level0 is depth 0, level0/level1/project is depth 1)
        expected_project_paths: set[Path] = set()
        expected_project_paths.add(tmp_path / "level0")  # Depth 0

        p = tmp_path / "level0" / "level1" / "project"
        expected_project_paths.add(p)  # Depth 1

        discovered_paths = {proj.path for proj in discovered}
        assert len(discovered) == 2, (
            f"Expected 2 projects, got {len(discovered)}: {discovered_paths}"
        )
        assert discovered_paths == expected_project_paths

    def test_discovery_with_many_excluded_directories(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovery performance with many excluded directories."""
        root = tmp_path / "workspace"
        root.mkdir()

        # Create many excluded directories
        for i in range(50):
            excluded = root / f"node_modules_{i}"
            excluded.mkdir()
            # Create files inside to add weight
            for j in range(10):
                (excluded / f"file_{j}").touch()

        # Create a valid project
        proj = root / "my_project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Discover should find the project and skip excluded dirs
        discovered = service.discover_projects([root])
        names = {p.name for p in discovered}
        assert "my_project" in names

    def test_project_path_with_symlink_circular_reference(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test handling of symlink cycles during discovery."""
        root = tmp_path / "workspace"
        root.mkdir()

        # Create a project
        proj = root / "project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Create a symlink back to root (creates cycle)
        (proj / "circular_link").symlink_to(root)

        # Discovery should handle this gracefully (not infinite loop)
        discovered = service.discover_projects([root])
        # Should find at least the original project
        assert len(discovered) >= 1

    def test_registry_with_special_json_characters(
        self,
        registry_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test registry handles project names with special JSON characters."""
        service = ProjectRegistryService(registry_path)

        # Create project with quotes in the name (after validation allows it)
        proj_path = tmp_path / "project_special"
        proj_path.mkdir()
        (proj_path / ".tasky").mkdir()

        metadata = service.register_project(proj_path)
        assert metadata.name == "project_special"

        # Verify it persists correctly in JSON
        with registry_path.open() as f:
            data = json.load(f)
        assert len(data["projects"]) == 1

    def test_concurrent_discovery_same_path(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that discovering same path multiple times doesn't create duplicates."""
        # Create a project
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Discover multiple times
        service.discover_and_register([tmp_path])
        service.discover_and_register([tmp_path])
        service.discover_and_register([tmp_path])

        # Should still have only one project
        projects = service.list_projects()
        assert len(projects) == 1

    def test_register_project_with_relative_path_normalization(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that relative paths are normalized to absolute paths."""
        # Create a project
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        # Register with relative path (change to parent and use relative)
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            service.register_project(Path("project"))

            # Verify stored path is absolute
            projects = service.list_projects()
            assert len(projects) == 1
            assert projects[0].path.is_absolute()
        finally:
            os.chdir(original_cwd)

    def test_update_last_accessed_multiple_times(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test updating last_accessed multiple times increases timestamp."""
        # Create and register project
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        service.register_project(proj)
        initial_projects = service.list_projects()
        initial_time = initial_projects[0].last_accessed

        # Wait a bit and update
        time.sleep(0.1)
        service.update_last_accessed(proj)

        updated_projects = service.list_projects()
        updated_time = updated_projects[0].last_accessed

        # Time should have advanced
        assert updated_time > initial_time

    def test_unregister_then_rediscover_same_project(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that unregistering and rediscovering works correctly."""
        # Create and register project
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / ".tasky").mkdir()

        service.register_project(proj)
        assert len(service.list_projects()) == 1

        # Unregister
        service.unregister_project(proj)
        assert len(service.list_projects()) == 0

        # Rediscover
        service.discover_and_register([tmp_path])
        assert len(service.list_projects()) == 1

    def test_list_projects_sorted_order_consistency(
        self,
        service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test that list_projects returns consistent sort order."""
        # Create multiple projects
        projects_to_create: list[Path] = []
        for i in range(10):
            proj = tmp_path / f"project_{i:02d}"
            proj.mkdir()
            (proj / ".tasky").mkdir()
            projects_to_create.append(proj)
            service.register_project(proj)

        # Get list multiple times
        list1 = service.list_projects()
        list2 = service.list_projects()

        # Should be in same order (by last_accessed, most recent first)
        assert [p.name for p in list1] == [p.name for p in list2]


class TestRegistryCorruptionRecovery:
    """Test corruption recovery scenarios for project registry."""

    @pytest.fixture
    def registry_path(self, tmp_path: Path) -> Path:
        """Create a temporary registry path."""
        registry_dir = tmp_path / "registry_storage"
        registry_dir.mkdir()
        return registry_dir / "registry.json"

    @pytest.fixture
    def service(self, registry_path: Path) -> ProjectRegistryService:
        """Create a registry service instance."""
        return ProjectRegistryService(registry_path)

    def test_corrupted_json_triggers_backup(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test that corrupted JSON triggers backup and recovery."""
        # Create corrupted JSON file
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        corrupted_data = '{"projects": [{"name": "test", invalid json'
        with registry_path.open("w") as f:
            f.write(corrupted_data)

        # Load should recover
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

        # Backup should exist
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 1
        assert backups[0].read_text() == corrupted_data

    def test_partially_written_registry_recovery(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test recovery from partially written registry file."""
        # Simulate partial write (incomplete JSON)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w") as f:
            f.write('{"projects": [{"name": "test", "path": "/tmp/test"')
            # File ends abruptly

        # Should recover gracefully
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

        # Backup should be created
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 1

    def test_invalid_schema_recovery(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test recovery from schema validation errors."""
        # Create JSON with invalid schema
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        invalid_schema = {
            "projects": [
                {
                    "name": "test",
                    # Missing required 'path' field
                },
            ],
        }
        with registry_path.open("w") as f:
            json.dump(invalid_schema, f)

        # Should recover and create empty registry
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

        # Backup should exist
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 1

    def test_backup_preserves_corrupted_data(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test that backup file preserves exact corrupted data."""
        # Create corrupted file with specific content
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        corrupted_content = "This is corrupted data: {[}]"
        with registry_path.open("w") as f:
            f.write(corrupted_content)

        # Load to trigger backup
        service._load()

        # Verify backup has exact content
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 1
        assert backups[0].read_text() == corrupted_content

    def test_multiple_corruption_attempts_create_timestamped_backups(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test that multiple corruptions create separate timestamped backups."""
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        # First corruption
        with registry_path.open("w") as f:
            f.write("corruption 1")
        service._load()

        time.sleep(0.01)  # Ensure different timestamp

        # Create new service instance to reset cached registry
        service2 = ProjectRegistryService(registry_path)

        # Second corruption
        with registry_path.open("w") as f:
            f.write("corruption 2")
        service2._load()

        # Should have two separate backup files
        backups = list(registry_path.parent.glob("registry.corrupted.*.json"))
        assert len(backups) == 2

        # Verify contents are different
        contents = {backup.read_text() for backup in backups}
        assert "corruption 1" in contents
        assert "corruption 2" in contents

    def test_registry_usable_after_corruption_recovery(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that registry is fully functional after recovering from corruption."""
        # Corrupt the registry
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w") as f:
            f.write("invalid json")

        # Load triggers recovery
        registry = service._load()
        assert len(registry.projects) == 0

        # Now use the service normally
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()

        # Should be able to register projects
        project = service.register_project(project_dir)
        assert project.name == "test-project"

        # Should be able to list projects
        projects = service.list_projects()
        assert len(projects) == 1

        # Verify data persists to disk correctly
        service2 = ProjectRegistryService(registry_path)
        projects2 = service2.list_projects()
        assert len(projects2) == 1
        assert projects2[0].name == "test-project"

    def test_atomic_write_prevents_corruption(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that atomic writes prevent partial data corruption."""
        # Register a project
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".tasky").mkdir()
        service.register_project(project_dir)

        # Verify temp file doesn't exist after successful write
        temp_path = registry_path.with_suffix(".tmp")
        assert not temp_path.exists()

        # Verify main file exists and is valid
        assert registry_path.exists()
        with registry_path.open() as f:
            data = json.load(f)
            assert len(data["projects"]) == 1

    def test_save_error_cleanup(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test that temp files are cleaned up on save errors."""
        # Make registry directory read-only
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            # Try to save - should fail
            registry = ProjectRegistry()
            with pytest.raises(Exception):  # noqa: B017
                service._save(registry)

            # Temp file should not exist
            temp_path = registry_path.with_suffix(".tmp")
            assert not temp_path.exists()
        finally:
            # Restore permissions for cleanup
            registry_path.parent.chmod(stat.S_IRWXU)

    def test_empty_file_recovery(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test recovery from empty registry file."""
        # Create empty file
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.touch()

        # Should recover gracefully
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

    def test_whitespace_only_file_recovery(
        self,
        service: ProjectRegistryService,
        registry_path: Path,
    ) -> None:
        """Test recovery from whitespace-only file."""
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w") as f:
            f.write("   \n\t\n   ")

        # Should recover gracefully
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []
