"""Dispatcher for task lifecycle hooks."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tasky_hooks.events import BaseEvent

logger = logging.getLogger("tasky.hooks")

Handler = Callable[["BaseEvent"], None]


class HookDispatcher:
    """Dispatches events to registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def register(self, event_type: str, handler: Handler) -> None:
        """Register a handler for a specific event type.

        Parameters
        ----------
        event_type : str
            The type of event to subscribe to (e.g., "task_created").
        handler : Handler
            The callable to execute when the event occurs.

        """
        self._handlers[event_type].append(handler)
        logger.debug("Registered handler for event: %s", event_type)

    def dispatch(self, event: BaseEvent) -> None:
        """Dispatch an event to all registered handlers.

        Handlers are executed synchronously in registration order. Exceptions
        raised by handlers are caught and logged, ensuring that one failing
        handler does not prevent others from running.

        Parameters
        ----------
        event : BaseEvent
            The event to dispatch.

        """
        event_type = event.event_type
        # Get handlers for specific event type and global handlers ("*")
        handlers = self._handlers.get(event_type, []) + self._handlers.get("*", [])

        if not handlers:
            logger.debug("No handlers registered for event: %s", event_type)
            return

        logger.debug("Dispatching event %s to %d handlers", event_type, len(handlers))

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Error executing hook handler for event %s",
                    event_type,
                )

    def reset(self) -> None:
        """Reset the dispatcher by clearing all registered handlers.

        This is primarily used for testing to ensure a clean state between tests.
        """
        self._handlers.clear()


# Global dispatcher instance
_dispatcher = HookDispatcher()


def get_dispatcher() -> HookDispatcher:
    """Get the global hook dispatcher instance."""
    return _dispatcher
