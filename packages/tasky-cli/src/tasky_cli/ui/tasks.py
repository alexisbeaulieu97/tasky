from __future__ import annotations

from typing import Iterable

from rich.table import Table
from tasky_core import FlattenedTask, flatten_tasks
from tasky_models import Task
from tasky_cli.ui.formatting import format_timestamp, shorten_id, status_label


def build_task_table(tasks: Iterable[Task]) -> Table:
    table = Table(title="Tasks", header_style="bold", show_lines=False)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Status", style="magenta")
    table.add_column("Updated", style="green")
    table.add_column("Details", style="dim", overflow="fold")

    for flat in flatten_tasks(list(tasks)):
        table.add_row(
            shorten_id(flat.task.task_id),
            format_task_name(flat),
            status_label(flat.task),
            format_timestamp(flat.task.updated_at),
            flat.task.details or "-",
        )
    return table


def format_task_name(flat: FlattenedTask) -> str:
    if flat.depth == 0:
        return flat.task.name
    prefix_parts: list[str] = []
    for is_last_ancestor in flat.lineage:
        prefix_parts.append("   " if is_last_ancestor else "│  ")
    connector = "└─ " if flat.is_last else "├─ "
    prefix_parts.append(connector)
    return "".join(prefix_parts) + flat.task.name
