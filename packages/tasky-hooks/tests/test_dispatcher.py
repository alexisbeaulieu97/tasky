"""Tests for hook dispatcher."""

from unittest.mock import Mock

from tasky_hooks.dispatcher import HookDispatcher
from tasky_hooks.events import BaseEvent


class MockEvent(BaseEvent):
    """Mock event for testing."""

    event_type: str = "mock_event"


def test_register_and_dispatch() -> None:
    """Test registering a handler and dispatching an event."""
    dispatcher = HookDispatcher()
    handler = Mock()

    dispatcher.register("mock_event", handler)

    event = MockEvent()
    dispatcher.dispatch(event)

    handler.assert_called_once_with(event)


def test_dispatch_no_handlers() -> None:
    """Test dispatching an event with no handlers."""
    dispatcher = HookDispatcher()
    event = MockEvent()

    # Should not raise exception
    dispatcher.dispatch(event)


def test_multiple_handlers() -> None:
    """Test multiple handlers for the same event."""
    dispatcher = HookDispatcher()
    handler1 = Mock()
    handler2 = Mock()

    dispatcher.register("mock_event", handler1)
    dispatcher.register("mock_event", handler2)

    event = MockEvent()
    dispatcher.dispatch(event)

    handler1.assert_called_once_with(event)
    handler2.assert_called_once_with(event)


def test_handler_error_isolation() -> None:
    """Test that one failing handler does not stop others."""
    dispatcher = HookDispatcher()

    failing_handler = Mock(side_effect=ValueError("Boom"))
    success_handler = Mock()

    dispatcher.register("mock_event", failing_handler)
    dispatcher.register("mock_event", success_handler)

    event = MockEvent()
    dispatcher.dispatch(event)

    failing_handler.assert_called_once_with(event)
    success_handler.assert_called_once_with(event)


def test_wildcard_handler() -> None:
    """Test wildcard handler receives all events."""
    dispatcher = HookDispatcher()
    wildcard_handler = Mock()
    specific_handler = Mock()

    dispatcher.register("*", wildcard_handler)
    dispatcher.register("mock_event", specific_handler)

    event = MockEvent()
    dispatcher.dispatch(event)

    wildcard_handler.assert_called_once_with(event)
    specific_handler.assert_called_once_with(event)
