"""Tests for project registry CLI commands."""

# ruff: noqa: ARG002
import shutil
import tomllib
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from tasky_cli.commands.projects import project_app
from tasky_projects.registry import ProjectRegistryService
from tasky_settings import AppSettings, ProjectRegistrySettings
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def mock_settings(tmp_path: Path) -> Iterator[AppSettings]:
    """Mock settings with temporary registry path."""
    registry_path = tmp_path / "registry.json"
    settings = AppSettings(
        project_registry=ProjectRegistrySettings(
            registry_path=registry_path,
            discovery_paths=[tmp_path / "projects"],
        ),
    )

    with patch("tasky_cli.commands.projects.get_settings", return_value=settings):
        yield settings


@pytest.fixture
def mock_registry_service(tmp_path: Path) -> Iterator[ProjectRegistryService]:
    """Mock registry service with temporary storage."""
    registry_path = tmp_path / "registry.json"
    service = ProjectRegistryService(registry_path)

    with patch("tasky_cli.commands.projects.get_project_registry_service", return_value=service):
        yield service


class TestListCommand:
    """Tests for the list command."""

    def test_list_empty_registry_no_discover(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing with empty registry and --no-discover flag."""
        result = runner.invoke(project_app, ["list", "--no-discover"])

        assert result.exit_code == 0
        assert "No projects found" in result.stdout
        assert "tasky project init" in result.stdout
        assert "tasky project discover" in result.stdout

    def test_list_empty_registry_auto_discover_no_projects(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing with empty registry triggers auto-discovery but finds nothing."""
        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        assert "Discovering projects" in result.stdout
        assert "No projects found" in result.stdout

    def test_list_empty_registry_auto_discover_finds_projects(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing with empty registry auto-discovers and registers projects."""
        # Create a discoverable project
        project_dir = tmp_path / "projects" / "test-project"
        (project_dir / ".tasky").mkdir(parents=True)

        result = runner.invoke(project_app, ["list"])

        assert result.exit_code == 0
        assert "Discovering projects" in result.stdout
        assert "Discovered and registered 1 project(s)" in result.stdout
        assert "Projects:" in result.stdout
        assert "test-project" in result.stdout

    def test_list_shows_registered_projects(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing shows all registered projects."""
        # Register some projects
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"
        (project1 / ".tasky").mkdir(parents=True)
        (project2 / ".tasky").mkdir(parents=True)

        mock_registry_service.register_project(project1)
        mock_registry_service.register_project(project2)

        result = runner.invoke(project_app, ["list", "--no-discover"])

        assert result.exit_code == 0
        assert "Projects:" in result.stdout
        assert "project1" in result.stdout
        assert "project2" in result.stdout
        assert "Last accessed:" in result.stdout

    def test_list_shows_missing_status(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test listing shows [MISSING] for projects with deleted directories."""
        # Register a project
        project_dir = tmp_path / "project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        # Delete the project directory
        shutil.rmtree(project_dir)

        result = runner.invoke(project_app, ["list", "--no-discover"])

        assert result.exit_code == 0
        assert "[MISSING]" in result.stdout
        assert "project" in result.stdout


class TestRegisterCommand:
    """Tests for the register command."""

    def test_register_valid_project(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering a valid project."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)

        result = runner.invoke(project_app, ["register", str(project_dir)])

        assert result.exit_code == 0
        assert "Project registered: my-project" in result.stdout
        assert str(project_dir) in result.stdout

    def test_register_nonexistent_path(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering a non-existent path fails."""
        project_dir = tmp_path / "nonexistent"

        result = runner.invoke(project_app, ["register", str(project_dir)])

        assert result.exit_code == 1
        # Typer writes errors to stdout, not stderr when using typer.echo(err=True)
        output = result.stdout + result.stderr
        assert "Error: Path does not exist" in output

    def test_register_file_not_directory(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering a file instead of directory fails."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        result = runner.invoke(project_app, ["register", str(file_path)])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Path is not a directory" in output

    def test_register_no_tasky_directory(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering a directory without .tasky subdirectory fails."""
        project_dir = tmp_path / "no-tasky"
        project_dir.mkdir()

        result = runner.invoke(project_app, ["register", str(project_dir)])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error:" in output

    def test_register_updates_existing_project(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test registering an already-registered project updates it."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)

        # Register once
        result1 = runner.invoke(project_app, ["register", str(project_dir)])
        assert result1.exit_code == 0

        # Register again
        result2 = runner.invoke(project_app, ["register", str(project_dir)])
        assert result2.exit_code == 0
        assert "Project registered: my-project" in result2.stdout


class TestUnregisterCommand:
    """Tests for the unregister command."""

    def test_unregister_with_yes_flag(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test unregistering a project with --yes flag skips confirmation."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        result = runner.invoke(project_app, ["unregister", "my-project", "--yes"])

        assert result.exit_code == 0
        assert "Project unregistered: my-project" in result.stdout

    def test_unregister_with_confirmation_yes(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test unregistering with confirmation accepted."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        result = runner.invoke(project_app, ["unregister", "my-project"], input="y\n")

        assert result.exit_code == 0
        assert "Are you sure you want to unregister this project?" in result.stdout
        assert "Project unregistered: my-project" in result.stdout

    def test_unregister_with_confirmation_no(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test unregistering with confirmation declined."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        # The runner doesn't properly handle interactive prompts, so we expect an abort
        result = runner.invoke(project_app, ["unregister", "my-project"], input="n\n")

        # Typer aborts with exit code 1 when confirmation is declined
        assert result.exit_code == 1
        assert "Cancelled" in result.stdout or "Aborted" in result.stdout

    def test_unregister_nonexistent_project(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
    ) -> None:
        """Test unregistering a non-existent project fails."""
        result = runner.invoke(project_app, ["unregister", "nonexistent", "--yes"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Project not found: nonexistent" in output
        assert "tasky project list" in output


class TestDiscoverCommand:
    """Tests for the discover command."""

    def test_discover_default_paths(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovering projects from default paths."""
        # Create a discoverable project
        project_dir = tmp_path / "projects" / "test-project"
        (project_dir / ".tasky").mkdir(parents=True)

        result = runner.invoke(project_app, ["discover"])

        assert result.exit_code == 0
        assert "Discovering projects" in result.stdout
        assert "Searching in:" in result.stdout
        assert "Discovered and registered 1 new project(s)" in result.stdout
        assert "test-project" in result.stdout

    def test_discover_custom_paths(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovering projects from custom paths."""
        # Create a discoverable project in a custom location
        custom_dir = tmp_path / "custom"
        project_dir = custom_dir / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)

        result = runner.invoke(project_app, ["discover", "--path", str(custom_dir)])

        assert result.exit_code == 0
        assert "Discovering projects" in result.stdout
        assert str(custom_dir) in result.stdout
        assert "Discovered and registered 1 new project(s)" in result.stdout

    def test_discover_no_new_projects(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovering when all projects are already registered."""
        # Create and register a project
        project_dir = tmp_path / "projects" / "test-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        result = runner.invoke(project_app, ["discover"])

        assert result.exit_code == 0
        assert "No new projects found" in result.stdout
        assert "Already tracking 1 project(s)" in result.stdout

    def test_discover_multiple_paths(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test discovering from multiple custom paths."""
        # Create projects in multiple locations
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        (dir1 / "project1" / ".tasky").mkdir(parents=True)
        (dir2 / "project2" / ".tasky").mkdir(parents=True)

        result = runner.invoke(
            project_app,
            ["discover", "--path", str(dir1), "--path", str(dir2)],
        )

        assert result.exit_code == 0
        assert "Discovered and registered 2 new project(s)" in result.stdout


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_new_project(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test initializing a new project."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["init"])

        assert result.exit_code == 0
        assert "Project initialized" in result.stdout
        assert (tmp_path / ".tasky" / "config.toml").exists()

    def test_init_with_custom_backend(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test initializing with a specific backend."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["init", "--backend", "sqlite"])

        assert result.exit_code == 0
        assert (tmp_path / ".tasky" / "config.toml").exists()
        # Verify backend in config
        with (tmp_path / ".tasky" / "config.toml").open("rb") as f:
            config = tomllib.load(f)
        assert config["storage"]["backend"] == "sqlite"

    def test_init_invalid_backend(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test initializing with an invalid backend."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["init", "--backend", "invalid"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Backend 'invalid' not registered" in output

    def test_init_overwrite_declined(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test declining to overwrite existing project."""
        config_file = tmp_path / ".tasky" / "config.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("[storage]\nbackend = 'json'\n")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["init"], input="n\n")

        assert result.exit_code == 0
        # Should not show "Project initialized" message after declining
        assert "Project initialized" not in result.stdout

    def test_init_overwrite_accepted(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test accepting to overwrite existing project."""
        config_file = tmp_path / ".tasky" / "config.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("[storage]\nbackend = 'json'\n")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["init", "--backend", "sqlite"], input="y\n")

        assert result.exit_code == 0
        assert "Project initialized" in result.stdout
        # Verify backend was updated
        with config_file.open("rb") as f:
            config = tomllib.load(f)
        assert config["storage"]["backend"] == "sqlite"


class TestInfoCommand:
    """Tests for the info command with project name."""

    def test_info_by_project_name(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test showing info for a project by name."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        result = runner.invoke(project_app, ["info", "--project-name", "my-project"])

        assert result.exit_code == 0
        assert "my-project" in result.stdout
        assert str(project_dir) in result.stdout
        assert "Created:" in result.stdout
        assert "Last accessed:" in result.stdout

    def test_info_by_project_name_not_found(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
    ) -> None:
        """Test showing info for a non-existent project name."""
        result = runner.invoke(project_app, ["info", "--project-name", "nonexistent"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "Error: Project 'nonexistent' not found" in output

    def test_info_by_project_name_missing_directory(
        self,
        mock_settings: AppSettings,
        mock_registry_service: ProjectRegistryService,
        tmp_path: Path,
    ) -> None:
        """Test showing info for a project with deleted directory."""
        project_dir = tmp_path / "my-project"
        (project_dir / ".tasky").mkdir(parents=True)
        mock_registry_service.register_project(project_dir)

        # Delete the directory
        shutil.rmtree(project_dir)

        result = runner.invoke(project_app, ["info", "--project-name", "my-project"])

        assert result.exit_code == 0
        output = result.stdout + result.stderr
        assert "[MISSING]" in output

    def test_info_current_directory(
        self,
        mock_settings: AppSettings,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test showing info for current directory project."""
        config_file = tmp_path / ".tasky" / "config.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("[storage]\nbackend = 'json'\npath = '.tasky/tasks.json'\n")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["info"])

        assert result.exit_code == 0
        assert "Project Information:" in result.stdout
        assert "Backend: json" in result.stdout

    def test_info_current_directory_no_project(
        self,
        mock_settings: AppSettings,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test showing info when no project exists in current directory."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(project_app, ["info"])

        assert result.exit_code == 1
        output = result.stdout + result.stderr
        assert "No project found in current directory" in output
