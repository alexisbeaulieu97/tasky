from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from tasky_models import Task


def format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local = value.astimezone()
    return local.strftime("%Y-%m-%d %H:%M")


def status_label(task: Task) -> str:
    return "[green]Completed[/green]" if task.completed else "[cyan]Pending[/cyan]"


def shorten_id(task_id: UUID) -> str:
    return str(task_id).split("-")[0]
