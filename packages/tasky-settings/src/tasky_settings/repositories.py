from __future__ import annotations

from dataclasses import dataclass

from tasky_core.projects import ProjectConfig, ProjectContext
from tasky_core.repositories import TaskRepository
from tasky_storage import JsonDocumentStore, JsonTaskRepository, SQLiteTaskRepository


@dataclass(frozen=True)
class TaskRepositoryFactory:
    """
    Builds task repositories based on project configuration.

    Defaults to JSON storage, switching to SQLite when the config points to
    a `.sqlite`/`.db` file. Callers may subclass/replace this factory to plug in
    alternate storage layers.
    """

    def build(self, context: ProjectContext, config: ProjectConfig) -> TaskRepository:
        tasks_path = config.tasks_file
        if not tasks_path.is_absolute():
            tasks_path = context.metadata_dir / tasks_path
        tasks_path = tasks_path.expanduser()
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        suffix = tasks_path.suffix.lower()
        if suffix in {".sqlite", ".db"}:
            return SQLiteTaskRepository(tasks_path)
        store = JsonDocumentStore(tasks_path)
        return JsonTaskRepository(store=store)
