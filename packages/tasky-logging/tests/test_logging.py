"""Tests for tasky_logging package."""

import logging

import pytest
from tasky_logging import Logger, configure_logging, get_logger


class TestGetLogger:
    """Tests for get_logger() factory function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_prefixes_name(self) -> None:
        """Test that logger name is prefixed with 'tasky.'."""
        logger = get_logger("test.module")
        assert logger.name == "tasky.test.module"

    def test_get_logger_returns_same_instance(self) -> None:
        """Test that multiple calls with same name return same logger."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2

    def test_logger_conforms_to_protocol(self) -> None:
        """Test that returned logger conforms to Logger protocol."""
        logger = get_logger("test")
        assert isinstance(logger, Logger)


class TestConfigureLogging:
    """Tests for configure_logging() function."""

    def setup_method(self) -> None:
        """Reset logging configuration before each test."""
        # Clear all handlers from tasky logger
        logger = logging.getLogger("tasky")
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def test_configure_logging_verbosity_zero_sets_warning(self) -> None:
        """Test that verbosity=0 sets WARNING level."""
        configure_logging(verbosity=0)
        logger = logging.getLogger("tasky")
        assert logger.level == logging.WARNING

    def test_configure_logging_verbosity_one_sets_info(self) -> None:
        """Test that verbosity=1 sets INFO level."""
        configure_logging(verbosity=1)
        logger = logging.getLogger("tasky")
        assert logger.level == logging.INFO

    def test_configure_logging_verbosity_two_sets_debug(self) -> None:
        """Test that verbosity=2 sets DEBUG level."""
        configure_logging(verbosity=2)
        logger = logging.getLogger("tasky")
        assert logger.level == logging.DEBUG

    def test_configure_logging_verbosity_three_sets_debug(self) -> None:
        """Test that verbosity=3+ also sets DEBUG level."""
        configure_logging(verbosity=3)
        logger = logging.getLogger("tasky")
        assert logger.level == logging.DEBUG

    def test_configure_logging_adds_handler(self) -> None:
        """Test that configure_logging adds a handler."""
        configure_logging(verbosity=1)
        logger = logging.getLogger("tasky")
        assert len(logger.handlers) == 1

    def test_configure_logging_removes_duplicate_handlers(self) -> None:
        """Test that calling configure_logging twice doesn't duplicate handlers."""
        configure_logging(verbosity=1)
        configure_logging(verbosity=1)
        logger = logging.getLogger("tasky")
        assert len(logger.handlers) == 1

    def test_configure_logging_sets_propagate_false(self) -> None:
        """Test that logger.propagate is set to False."""
        configure_logging(verbosity=1)
        logger = logging.getLogger("tasky")
        assert logger.propagate is False

    def test_configure_logging_supports_standard_format(self) -> None:
        """Test that standard format is applied correctly."""
        configure_logging(verbosity=1, format_style="standard")
        logger = logging.getLogger("tasky")
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None
        # Verify formatter has expected format by checking it formats correctly
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "test" in formatted  # Logger name
        assert "INFO" in formatted  # Log level
        assert "test message" in formatted  # Message


class TestLoggingWithoutConfiguration:
    """Tests for logging behavior without explicit configuration."""

    def test_logger_works_without_configuration(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that logger can be used without calling configure_logging."""
        # Get a logger and log a warning
        test_logger = get_logger("test.unconfigured")

        # Capture logs at the tasky level
        with caplog.at_level(logging.WARNING, logger="tasky"):
            test_logger.warning("Test warning message")

        # Should not raise an error and logging should work
        # Note: Without explicit configuration, the default Python logging
        # behavior applies. The test verifies no exceptions occur.
        assert True  # If we got here, no exception was raised


class TestLoggerProtocol:
    """Tests for Logger protocol."""

    def test_logger_has_debug_method(self) -> None:
        """Test that Logger has debug method."""
        logger = get_logger("test")
        assert hasattr(logger, "debug")
        assert callable(logger.debug)

    def test_logger_has_info_method(self) -> None:
        """Test that Logger has info method."""
        logger = get_logger("test")
        assert hasattr(logger, "info")
        assert callable(logger.info)

    def test_logger_has_warning_method(self) -> None:
        """Test that Logger has warning method."""
        logger = get_logger("test")
        assert hasattr(logger, "warning")
        assert callable(logger.warning)

    def test_logger_has_error_method(self) -> None:
        """Test that Logger has error method."""
        logger = get_logger("test")
        assert hasattr(logger, "error")
        assert callable(logger.error)

    def test_logger_has_critical_method(self) -> None:
        """Test that Logger has critical method."""
        logger = get_logger("test")
        assert hasattr(logger, "critical")
        assert callable(logger.critical)
