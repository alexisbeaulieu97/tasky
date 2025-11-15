"""Tests for ProjectRegistryService."""
# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

import json
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
        """Test loading corrupted registry file."""
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w") as f:
            f.write("not valid json{")

        # Should return empty registry
        registry = service._load()
        assert isinstance(registry, ProjectRegistry)
        assert registry.projects == []

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
