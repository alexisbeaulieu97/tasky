"""Tests for custom settings sources."""

from pathlib import Path

from tasky_settings.models import AppSettings
from tasky_settings.sources import (
    GlobalConfigSource,
    ProjectConfigSource,
    TomlConfigSource,
)


class TestTomlConfigSource:
    """Tests for TomlConfigSource base class."""

    def test_loads_valid_toml_file(self, tmp_path: Path) -> None:
        """Test that valid TOML files are loaded correctly."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 1
            format = "json"

            [task_defaults]
            priority = 5
            status = "in-progress"
            """,
        )

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        assert config["logging"]["verbosity"] == 1
        assert config["logging"]["format"] == "json"
        assert config["task_defaults"]["priority"] == 5

    def test_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """Test that missing files return empty dict without error."""
        config_file = tmp_path / "nonexistent.toml"

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        assert config == {}

    def test_handles_malformed_toml_gracefully(self, tmp_path: Path) -> None:
        """Test that malformed TOML returns empty dict with warning."""
        config_file = tmp_path / "bad.toml"
        config_file.write_text("this is not valid TOML [[[")

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        # Should return empty dict and not raise exception
        assert config == {}

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Test that empty files are handled correctly."""
        config_file = tmp_path / "empty.toml"
        config_file.write_text("")

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        assert config == {}

    def test_nested_sections(self, tmp_path: Path) -> None:
        """Test that nested TOML sections are parsed correctly."""
        config_file = tmp_path / "nested.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 2

            [task_defaults]
            priority = 4
            status = "done"
            """,
        )

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        assert config["logging"]["verbosity"] == 2
        assert config["task_defaults"]["priority"] == 4
        assert config["task_defaults"]["status"] == "done"

    def test_comments_are_supported(self, tmp_path: Path) -> None:
        """Test that TOML comments are parsed correctly."""
        config_file = tmp_path / "commented.toml"
        config_file.write_text(
            """
            # Logging configuration
            [logging]
            verbosity = 1  # INFO level
            """,
        )

        source = TomlConfigSource(AppSettings, config_file)
        config = source()

        assert config["logging"]["verbosity"] == 1


class TestGlobalConfigSource:
    """Tests for GlobalConfigSource."""

    def test_uses_home_directory_path(self) -> None:
        """Test that GlobalConfigSource targets ~/.tasky/config.toml."""
        source = GlobalConfigSource(AppSettings)

        expected_path = Path.home() / ".tasky" / "config.toml"
        assert source.file_path == expected_path

    def test_loads_from_home_directory(self) -> None:
        """Test loading config from home directory (if it exists)."""
        source = GlobalConfigSource(AppSettings)
        config = source()

        # Should return dict (empty if file doesn't exist)
        assert isinstance(config, dict)


class TestProjectConfigSource:
    """Tests for ProjectConfigSource."""

    def test_uses_project_root_parameter(self, tmp_path: Path) -> None:
        """Test that explicit project root is used."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        source = ProjectConfigSource(AppSettings, project_root=project_root)

        expected_path = project_root / ".tasky" / "config.toml"
        assert source.file_path == expected_path

    def test_defaults_to_current_directory(self) -> None:
        """Test that current directory is used by default."""
        source = ProjectConfigSource(AppSettings)

        expected_path = Path.cwd() / ".tasky" / "config.toml"
        assert source.file_path == expected_path

    def test_loads_from_project_directory(self, tmp_path: Path) -> None:
        """Test loading config from project directory."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        config_dir = project_root / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 2
            """,
        )

        source = ProjectConfigSource(AppSettings, project_root=project_root)
        config = source()

        assert config["logging"]["verbosity"] == 2

    def test_missing_project_config_returns_empty(self, tmp_path: Path) -> None:
        """Test that missing project config returns empty dict."""
        project_root = tmp_path / "empty_project"
        project_root.mkdir()

        source = ProjectConfigSource(AppSettings, project_root=project_root)
        config = source()

        assert config == {}


class TestSourceIntegration:
    """Integration tests for multiple sources working together."""

    def test_sources_can_be_instantiated_together(self, tmp_path: Path) -> None:
        """Test that global and project sources can coexist."""
        global_source = GlobalConfigSource(AppSettings)
        project_source = ProjectConfigSource(AppSettings, project_root=tmp_path)

        global_config = global_source()
        project_config = project_source()

        assert isinstance(global_config, dict)
        assert isinstance(project_config, dict)
