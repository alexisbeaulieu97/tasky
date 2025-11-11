"""Commands related to task management in Tasky CLI."""

from pathlib import Path

import typer
from tasky_storage.backends.json.repository import JsonTaskRepository
from tasky_tasks.service import TaskService

task_app = typer.Typer(no_args_is_help=True)


@task_app.command(name="list")
def list_command() -> None:
    """List all tasks."""
    storage_path = Path(".tasky/tasks.json")

    if not storage_path.exists():
        typer.echo(f"No tasks found in {storage_path}")
        return

    service = TaskService(JsonTaskRepository.from_path(storage_path))
    tasks = service.get_all_tasks()
    for task in tasks:
        typer.echo(f"{task.name} - {task.details}")
