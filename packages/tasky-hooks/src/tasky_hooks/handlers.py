"""Default hook handlers."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tasky_hooks.events import BaseEvent

logger = logging.getLogger("tasky.hooks.handlers")


def logging_handler(event: BaseEvent) -> None:
    """Log all events to the application log."""
    task_id = getattr(event, "task_id", "N/A")
    logger.info("Event received: %s (id=%s)", event.event_type, task_id)
    logger.debug("Event payload: %s", event.model_dump_json())


def echo_handler(event: BaseEvent) -> None:
    """Print event details to stdout.

    This handler is intended for use with the --verbose-hooks CLI flag.
    """
    print(f"Hook: {event.event_type} fired", file=sys.stdout)  # noqa: T201
    print(f"  Timestamp: {event.timestamp}", file=sys.stdout)  # noqa: T201

    if hasattr(event, "task_id"):
        # We use getattr to avoid type checking errors on BaseEvent
        task_id = getattr(event, "task_id")  # noqa: B009
        print(f"  Task ID: {task_id}", file=sys.stdout)  # noqa: T201

    # Print event-specific details if available
    if hasattr(event, "task_snapshot"):
        # We know it has task_snapshot, but mypy doesn't know the type
        snapshot = getattr(event, "task_snapshot")  # noqa: B009
        print(f"  Task: {snapshot.name}", file=sys.stdout)  # noqa: T201
        print(f"  Status: {snapshot.status}", file=sys.stdout)  # noqa: T201

    if event.event_type == "task_updated" and hasattr(event, "updated_fields"):
        # Cast to TaskUpdatedEvent for type safety if needed, or just use getattr
        updated_fields = getattr(event, "updated_fields")  # noqa: B009
        print(f"  Updated fields: {updated_fields}", file=sys.stdout)  # noqa: T201
