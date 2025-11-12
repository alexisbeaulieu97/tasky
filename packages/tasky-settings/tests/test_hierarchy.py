"""Integration tests for hierarchical settings precedence."""

from pathlib import Path

import pytest
from tasky_settings import get_settings


class TestSettingsPrecedence:
    """Tests for settings precedence rules."""

    def test_default_settings_without_config(self) -> None:
        """Test that default values are used when no config exists."""
        settings = get_settings()

        assert settings.logging.verbosity == 0
        assert settings.logging.format == "standard"
        assert settings.task_defaults.priority == 3
        assert settings.task_defaults.status == "pending"

    def test_project_config_overrides_defaults(self, tmp_path: Path) -> None:
        """Test that project config overrides model defaults."""
        # Create project config
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 2
            """,
        )

        settings = get_settings(project_root=tmp_path)

        assert settings.logging.verbosity == 2
        assert settings.logging.format == "standard"  # Default preserved

    def test_cli_overrides_take_highest_precedence(self, tmp_path: Path) -> None:
        """Test that CLI overrides take precedence over all other sources."""
        # Create project config
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 1
            """,
        )

        cli_overrides = {"logging": {"verbosity": 2}}
        settings = get_settings(project_root=tmp_path, cli_overrides=cli_overrides)

        assert settings.logging.verbosity == 2  # CLI wins

    def test_env_vars_override_file_configs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that environment variables override file configs."""
        # Create project config
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 0
            """,
        )

        # Set environment variable
        monkeypatch.setenv("TASKY_LOGGING__VERBOSITY", "2")

        settings = get_settings(project_root=tmp_path)

        assert settings.logging.verbosity == 2  # Env var wins

    def test_cli_overrides_beat_env_vars(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that CLI overrides beat environment variables."""
        # Set environment variable
        monkeypatch.setenv("TASKY_LOGGING__VERBOSITY", "1")

        # CLI overrides
        cli_overrides = {"logging": {"verbosity": 2}}

        settings = get_settings(project_root=tmp_path, cli_overrides=cli_overrides)

        assert settings.logging.verbosity == 2  # CLI wins over env

    def test_partial_project_config_merging(self, tmp_path: Path) -> None:
        """Test that project config only overrides specified fields."""
        # Create project config with only verbosity
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 2
            """,
        )

        settings = get_settings(project_root=tmp_path)

        assert settings.logging.verbosity == 2  # From project config
        assert settings.logging.format == "standard"  # Default preserved
        assert settings.task_defaults.priority == 3  # Other section untouched

    def test_complete_precedence_chain(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test complete precedence: defaults → project → env → CLI."""
        # Create project config
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 1
            format = "json"

            [task_defaults]
            priority = 4
            """,
        )

        # Set env var for format (should override project)
        monkeypatch.setenv("TASKY_LOGGING__FORMAT", "minimal")

        # CLI override for verbosity (should override everything)
        cli_overrides = {"logging": {"verbosity": 2}}

        settings = get_settings(project_root=tmp_path, cli_overrides=cli_overrides)

        assert settings.logging.verbosity == 2  # From CLI
        assert settings.logging.format == "minimal"  # From env var
        assert settings.task_defaults.priority == 4  # From project config
        assert settings.task_defaults.status == "pending"  # Default


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_invalid_config_values_raise_errors(self, tmp_path: Path) -> None:
        """Test that invalid config values raise validation errors."""
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 5
            """,
        )

        with pytest.raises(Exception, match=r"validation|less than or equal") as exc_info:
            get_settings(project_root=tmp_path)

        # Should mention validation error
        error_str = str(exc_info.value)
        assert "validation" in error_str.lower() or "less than or equal" in error_str

    def test_invalid_field_type_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid field types raise validation errors."""
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = "high"
            """,
        )

        with pytest.raises(Exception, match=r"int|Input should be") as exc_info:
            get_settings(project_root=tmp_path)

        # Should mention type error
        error_str = str(exc_info.value)
        assert "validation" in error_str.lower() or "int" in error_str.lower()

    def test_unknown_fields_are_ignored(self, tmp_path: Path) -> None:
        """Test that unknown fields in config don't cause errors."""
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text(
            """
            [logging]
            verbosity = 1
            unknown_field = true
            """,
        )

        settings = get_settings(project_root=tmp_path)

        # Should load successfully, ignoring unknown field
        assert settings.logging.verbosity == 1


class TestProjectRootParameter:
    """Tests for project_root parameter."""

    def test_explicit_project_root_is_used(self, tmp_path: Path) -> None:
        """Test that explicit project root parameter is respected."""
        project_a = tmp_path / "project_a"
        project_a.mkdir()
        config_dir_a = project_a / ".tasky"
        config_dir_a.mkdir()
        config_file_a = config_dir_a / "config.toml"
        config_file_a.write_text(
            """
            [logging]
            verbosity = 1
            """,
        )

        project_b = tmp_path / "project_b"
        project_b.mkdir()
        config_dir_b = project_b / ".tasky"
        config_dir_b.mkdir()
        config_file_b = config_dir_b / "config.toml"
        config_file_b.write_text(
            """
            [logging]
            verbosity = 2
            """,
        )

        settings_a = get_settings(project_root=project_a)
        settings_b = get_settings(project_root=project_b)

        assert settings_a.logging.verbosity == 1
        assert settings_b.logging.verbosity == 2

    def test_none_project_root_uses_current_directory(self) -> None:
        """Test that None project_root defaults to current directory."""
        settings = get_settings(project_root=None)

        # Should work without error
        assert isinstance(settings.logging.verbosity, int)


class TestEnvironmentVariables:
    """Tests for environment variable support."""

    def test_env_var_nested_delimiter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that environment variables use double underscore for nesting."""
        monkeypatch.setenv("TASKY_LOGGING__VERBOSITY", "2")
        monkeypatch.setenv("TASKY_LOGGING__FORMAT", "json")
        monkeypatch.setenv("TASKY_TASK_DEFAULTS__PRIORITY", "5")

        settings = get_settings(project_root=tmp_path)

        assert settings.logging.verbosity == 2
        assert settings.logging.format == "json"
        assert settings.task_defaults.priority == 5

    def test_env_var_prefix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that only TASKY_ prefixed vars are recognized."""
        monkeypatch.setenv("TASKY_LOGGING__VERBOSITY", "2")
        monkeypatch.setenv("OTHER_LOGGING__VERBOSITY", "1")  # Should be ignored

        settings = get_settings(project_root=tmp_path)

        assert settings.logging.verbosity == 2  # TASKY_ var used


class TestMissingConfigs:
    """Tests for behavior with missing configuration files."""

    def test_missing_configs_use_defaults(self, tmp_path: Path) -> None:
        """Test that missing config files don't cause errors."""
        # tmp_path has no .tasky directory
        settings = get_settings(project_root=tmp_path)

        # Should use defaults
        assert settings.logging.verbosity == 0
        assert settings.logging.format == "standard"
        assert settings.task_defaults.priority == 3

    def test_empty_config_file(self, tmp_path: Path) -> None:
        """Test that empty config files work correctly."""
        config_dir = tmp_path / ".tasky"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text("")

        settings = get_settings(project_root=tmp_path)

        # Should use defaults
        assert settings.logging.verbosity == 0
