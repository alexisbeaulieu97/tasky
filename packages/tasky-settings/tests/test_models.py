"""Tests for settings models."""

import pytest
from pydantic import ValidationError
from tasky_settings.models import AppSettings, LoggingSettings, TaskDefaultsSettings


class TestLoggingSettings:
    """Tests for LoggingSettings model."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = LoggingSettings()
        assert settings.verbosity == 0
        assert settings.format == "standard"

    def test_valid_verbosity_values(self) -> None:
        """Test that valid verbosity values are accepted."""
        for verbosity in [0, 1, 2]:
            settings = LoggingSettings(verbosity=verbosity)
            assert settings.verbosity == verbosity

    def test_invalid_verbosity_too_low(self) -> None:
        """Test that verbosity below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(verbosity=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_invalid_verbosity_too_high(self) -> None:
        """Test that verbosity above 2 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(verbosity=3)
        assert "less than or equal to 2" in str(exc_info.value)

    def test_invalid_verbosity_type(self) -> None:
        """Test that non-integer verbosity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(verbosity="high")  # type: ignore[arg-type]
        assert "int" in str(exc_info.value).lower()

    def test_valid_format_values(self) -> None:
        """Test that valid format values are accepted."""
        for fmt in ["standard", "json", "minimal"]:
            settings = LoggingSettings(format=fmt)  # type: ignore[arg-type]
            assert settings.format == fmt

    def test_invalid_format_value(self) -> None:
        """Test that invalid format values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(format="unknown")  # type: ignore[arg-type]
        assert "standard" in str(exc_info.value)
        assert "json" in str(exc_info.value)
        assert "minimal" in str(exc_info.value)


class TestTaskDefaultsSettings:
    """Tests for TaskDefaultsSettings model."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        settings = TaskDefaultsSettings()
        assert settings.priority == 3
        assert settings.status == "pending"

    def test_valid_priority_values(self) -> None:
        """Test that valid priority values are accepted."""
        for priority in [1, 2, 3, 4, 5]:
            settings = TaskDefaultsSettings(priority=priority)
            assert settings.priority == priority

    def test_invalid_priority_too_low(self) -> None:
        """Test that priority below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskDefaultsSettings(priority=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_invalid_priority_too_high(self) -> None:
        """Test that priority above 5 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskDefaultsSettings(priority=6)
        assert "less than or equal to 5" in str(exc_info.value)

    def test_custom_status(self) -> None:
        """Test that custom status values are accepted."""
        settings = TaskDefaultsSettings(status="in_progress")
        assert settings.status == "in_progress"


class TestAppSettings:
    """Tests for AppSettings model."""

    def test_default_values(self) -> None:
        """Test that default subsystem settings are initialized."""
        settings = AppSettings()
        assert isinstance(settings.logging, LoggingSettings)
        assert isinstance(settings.task_defaults, TaskDefaultsSettings)
        assert settings.logging.verbosity == 0
        assert settings.task_defaults.priority == 3

    def test_custom_logging_settings(self) -> None:
        """Test that custom logging settings can be provided."""
        settings = AppSettings(logging={"verbosity": 2, "format": "json"})  # type: ignore[arg-type]
        assert settings.logging.verbosity == 2
        assert settings.logging.format == "json"

    def test_custom_task_defaults(self) -> None:
        """Test that custom task defaults can be provided."""
        settings = AppSettings(task_defaults={"priority": 5, "status": "active"})  # type: ignore[arg-type]
        assert settings.task_defaults.priority == 5
        assert settings.task_defaults.status == "active"

    def test_env_prefix_configuration(self) -> None:
        """Test that model config has correct env prefix."""
        # Pydantic's model_config is dict at runtime but typed as SettingsConfigDict
        assert AppSettings.model_config["env_prefix"] == "TASKY_"  # type: ignore[typeddict-item]

    def test_env_nested_delimiter_configuration(self) -> None:
        """Test that model config has correct nested delimiter."""
        # Pydantic's model_config is dict at runtime but typed as SettingsConfigDict
        assert AppSettings.model_config["env_nested_delimiter"] == "__"  # type: ignore[typeddict-item]

    def test_unknown_fields_ignored(self) -> None:
        """Test that unknown fields are ignored (extra='ignore')."""
        settings = AppSettings(unknown_field="value")  # type: ignore[call-arg]
        assert not hasattr(settings, "unknown_field")
        # Should not raise validation error

    def test_partial_override(self) -> None:
        """Test that partial config overrides work correctly."""
        settings = AppSettings(logging={"verbosity": 1})  # type: ignore[arg-type]
        assert settings.logging.verbosity == 1
        assert settings.logging.format == "standard"  # default preserved
        assert settings.task_defaults.priority == 3  # other section unaffected
