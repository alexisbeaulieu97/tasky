from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from tasky_core import TaskService, count_tasks
from tasky_core.projects import (
    PROJECT_CONFIG_FILENAME as CORE_CONFIG_FILENAME,
    PROJECTS_REGISTRY_FILENAME as CORE_REGISTRY_FILENAME,
    ProjectConfig,
    ProjectContext,
    ProjectRegistryEntry,
    ProjectInitialisationError,
    ProjectSettingsError,
    ProjectRegistryError,
    RegistryBackend,
    ensure_project_initialised as core_ensure_project_initialised,
    get_project_context as core_get_project_context,
    initialise_project as core_initialise_project,
    list_registered_projects as core_list_registered_projects,
    load_project_config as core_load_project_config,
    prune_missing_projects as core_prune_missing_projects,
    register_project as core_register_project,
    save_project_config as core_save_project_config,
    unregister_project as core_unregister_project,
    update_project_progress as core_update_project_progress,
)
from tasky_core.repositories import TaskRepository, TaskRepositoryError
from tasky_core.hooks import (
    HookBusPort,
    HookEvent,
    ProjectPostForgetPayload,
    ProjectPostInitPayload,
)
from tasky_core.projects.registry import ProjectRegistryRepository
from tasky_core.projects.ports import ProjectConfigStore, TaskBootstrapper
from tasky_storage import load_project_hook_bus

from . import resolve_tasky_dir, settings as global_settings
from .registry_repositories import ProjectRegistryRepositoryFactory
from .repositories import TaskRepositoryFactory
from .project_io import FileProjectConfigStore, FileTaskBootstrapper

REGISTRY_FILENAME = CORE_REGISTRY_FILENAME
REGISTRY_SQLITE_FILENAME = "projects.db"
PROJECT_CONFIG_FILENAME = CORE_CONFIG_FILENAME


class ProjectSettingsService:
    def __init__(
        self,
        *,
        tasky_dir: Path | None = None,
        registry_backend: RegistryBackend | None = None,
        repository_factory: TaskRepositoryFactory | None = None,
        registry_repository_factory: ProjectRegistryRepositoryFactory | None = None,
        hook_bus_factory: Callable[[ProjectContext], HookBusPort] | None = None,
        config_store: ProjectConfigStore | None = None,
        task_bootstrapper: TaskBootstrapper | None = None,
    ) -> None:
        self._tasky_dir = resolve_tasky_dir(tasky_dir)
        self._registry_backend: RegistryBackend = (
            registry_backend or global_settings.registry_backend
        )
        self._json_registry_path = self._tasky_dir / REGISTRY_FILENAME
        self._sqlite_registry_path = self._tasky_dir / REGISTRY_SQLITE_FILENAME
        self._repository_factory = repository_factory or TaskRepositoryFactory()
        self._registry_repository_factory = (
            registry_repository_factory or ProjectRegistryRepositoryFactory()
        )
        self._hook_bus_factory = hook_bus_factory or _default_hook_bus_factory
        self._config_store = config_store or FileProjectConfigStore()
        self._task_bootstrapper = task_bootstrapper or FileTaskBootstrapper()
        self._ensure_registry_backend_ready()

    @property
    def registry_path(self) -> Path:
        if self._registry_backend == "sqlite":
            return self._sqlite_registry_path
        return self._json_registry_path

    @property
    def registry_backend(self) -> RegistryBackend:
        return self._registry_backend

    def initialise_project(
        self,
        project_path: Path | None = None,
        *,
        force: bool = False,
    ) -> ProjectContext:
        target_path = project_path or Path.cwd()
        already_initialised = self.is_project_initialised(target_path)
        context = core_initialise_project(
            target_path,
            force=force,
            config_store=self._config_store,
            task_bootstrapper=self._task_bootstrapper,
        )
        repository = self._registry_repository()
        core_register_project(
            context.project_path,
            repository=repository,
        )
        self._emit_project_event(
            context,
            HookEvent.PROJECT_POST_INIT,
            ProjectPostInitPayload(reinitialised=already_initialised),
        )
        repo = self.get_task_repository(context.project_path)
        self._refresh_progress_from_repository(context, repo)
        return context

    def ensure_project_initialised(self, project_path: Path | None = None) -> ProjectContext:
        context = core_get_project_context(project_path)
        core_ensure_project_initialised(context)
        return context

    def is_project_initialised(self, project_path: Path | None = None) -> bool:
        context = core_get_project_context(project_path)
        return context.config_path.exists()

    def load_project_config(self, project_path: Path | None = None) -> ProjectConfig:
        context = core_get_project_context(project_path)
        return core_load_project_config(context, config_store=self._config_store)

    def save_project_config(
        self,
        config: ProjectConfig,
        project_path: Path | None = None,
    ) -> Path:
        context = core_get_project_context(project_path)
        core_save_project_config(config, context, config_store=self._config_store)
        return context.config_path

    def update_project_config(
        self,
        *,
        project_path: Path | None = None,
        updates: Mapping[str, Any] | None = None,
        force: bool = False,
    ) -> ProjectConfig:
        context = core_get_project_context(project_path)
        core_ensure_project_initialised(context)
        current = core_load_project_config(context, config_store=self._config_store)
        if not updates:
            return current
        applied_updates = self._normalise_config_updates(updates)
        if not applied_updates:
            return current
        updated_config = current.model_copy(update=applied_updates)
        if current.tasks_file == updated_config.tasks_file:
            self._persist_config(context, updated_config)
            return updated_config
        self._handle_tasks_file_change(
            context,
            current_config=current,
            updated_config=updated_config,
            force=force,
        )
        return updated_config

    def _normalise_config_updates(self, updates: Mapping[str, Any]) -> dict[str, Any]:
        allowed_keys = {"tasks_file"}
        unknown = set(updates.keys()) - allowed_keys
        if unknown:
            unknown_keys = ", ".join(sorted(unknown))
            raise ProjectSettingsError(
                f"Unsupported config key(s): {unknown_keys}. "
                "Only 'tasks_file' can be updated via this command."
            )
        payload: dict[str, Any] = {}
        if "tasks_file" in updates:
            value = updates["tasks_file"]
            payload["tasks_file"] = Path(str(value))
        return payload

    def _persist_config(self, context: ProjectContext, config: ProjectConfig) -> None:
        core_save_project_config(config, context, config_store=self._config_store)
        self._touch_registry_entry(context.project_path)

    def _handle_tasks_file_change(
        self,
        context: ProjectContext,
        *,
        current_config: ProjectConfig,
        updated_config: ProjectConfig,
        force: bool,
    ) -> None:
        self._migrate_tasks_dataset(
            context,
            current_config=current_config,
            updated_config=updated_config,
            force=force,
        )
        self._persist_config(context, updated_config)
        repository = self._repository_factory.build(context, updated_config)
        self._refresh_progress_from_repository(context, repository)

    def refresh_project_progress(
        self,
        project_path: Path | None = None,
    ) -> tuple[int, int] | None:
        try:
            context = self.ensure_project_initialised(project_path)
        except ProjectInitialisationError:
            return None
        repository = self.get_task_repository(context.project_path)
        return self._refresh_progress_from_repository(context, repository)

    def get_task_repository(self, project_path: Path | None = None) -> TaskRepository:
        context = self.ensure_project_initialised(project_path)
        config = self.load_project_config(context.project_path)
        return self._repository_factory.build(context, config)

    def build_task_service(self, project_path: Path | None = None) -> TaskService:
        context = self.ensure_project_initialised(project_path)
        hook_bus = self._hook_bus(context)
        config = self.load_project_config(context.project_path)
        repository = self._repository_factory.build(context, config)

        def _refresh() -> None:
            self._refresh_progress_from_repository(context, repository)
        return _ProgressAwareTaskService(
            repository=repository,
            hook_bus=hook_bus,
            refresh_callback=_refresh,
        )

    def register_project(self, project_path: Path) -> ProjectRegistryEntry:
        repository = self._registry_repository()
        entry = core_register_project(
            project_path,
            repository=repository,
        )
        self.refresh_project_progress(project_path)
        return entry

    def unregister_project(self, project_path: Path, *, purge: bool = False) -> None:
        context = self.get_project_context(project_path)
        repository = self._registry_repository()
        core_unregister_project(
            project_path,
            repository=repository,
        )
        self._emit_project_event(
            context,
            HookEvent.PROJECT_POST_FORGET,
            ProjectPostForgetPayload(purged=purge),
        )
        if purge and context.metadata_dir.exists():
            shutil.rmtree(context.metadata_dir, ignore_errors=True)

    def list_registered_projects(
        self,
        *,
        include_missing: bool = False,
    ) -> Iterable[ProjectRegistryEntry]:
        repository = self._registry_repository()
        return core_list_registered_projects(
            repository,
            include_missing=include_missing,
        )

    def prune_missing_projects(self) -> list[ProjectRegistryEntry]:
        repository = self._registry_repository()
        return core_prune_missing_projects(
            repository,
        )

    def get_project_context(self, project_path: Path | None = None) -> ProjectContext:
        return core_get_project_context(project_path)

    def _registry_repository(
        self,
        *,
        path: Path | None = None,
        backend: RegistryBackend | None = None,
    ) -> ProjectRegistryRepository:
        target_path = path or self.registry_path
        target_backend = backend or self.registry_backend
        return self._registry_repository_factory.build(target_path, target_backend)

    def _touch_registry_entry(self, project_path: Path) -> None:
        repository = self._registry_repository()
        core_register_project(project_path, repository=repository)

    def _resolve_tasks_path(self, context: ProjectContext, config: ProjectConfig) -> Path:
        tasks_path = config.tasks_file
        if not tasks_path.is_absolute():
            tasks_path = context.metadata_dir / tasks_path
        return tasks_path.expanduser()

    def _migrate_tasks_dataset(
        self,
        context: ProjectContext,
        *,
        current_config: ProjectConfig,
        updated_config: ProjectConfig,
        force: bool,
    ) -> None:
        old_path = self._resolve_tasks_path(context, current_config)
        new_path = self._resolve_tasks_path(context, updated_config)
        if old_path == new_path:
            return
        self._validate_tasks_destination(old_path, new_path, force)
        tasks = self._load_tasks_for_migration(context, current_config)
        self._write_tasks_to_destination(context, updated_config, tasks)

    def _validate_tasks_destination(
        self,
        old_path: Path,
        new_path: Path,
        force: bool,
    ) -> None:
        if not new_path.exists():
            return
        if new_path.is_dir():
            raise ProjectSettingsError(
                f"Tasks file must be a file path, received directory: {new_path}"
            )
        if not force:
            raise ProjectSettingsError(
                f"Tasks file already exists at {new_path}. "
                "Re-run with '--force' to overwrite or choose a different path."
            )
        if new_path != old_path and new_path.is_file():
            new_path.unlink()

    def _load_tasks_for_migration(
        self,
        context: ProjectContext,
        config: ProjectConfig,
    ) -> list:
        try:
            current_repo = self._repository_factory.build(context, config)
            return current_repo.list_tasks()
        except TaskRepositoryError as exc:
            raise ProjectSettingsError(
                "Unable to read existing tasks before migrating storage."
            ) from exc

    def _write_tasks_to_destination(
        self,
        context: ProjectContext,
        config: ProjectConfig,
        tasks: list,
    ) -> None:
        try:
            new_repo = self._repository_factory.build(context, config)
            new_repo.replace_tasks(tasks)
        except TaskRepositoryError as exc:
            raise ProjectSettingsError(
                "Failed to migrate tasks to the new storage file."
            ) from exc

    def _refresh_progress_from_repository(
        self,
        context: ProjectContext,
        repository: TaskRepository,
    ) -> tuple[int, int] | None:
        try:
            tasks = repository.list_tasks()
        except TaskRepositoryError:
            return None
        remaining, total = count_tasks(tasks)
        completed = total - remaining
        self._update_registry_progress(context.project_path, total, completed)
        return (remaining, total)

    def _update_registry_progress(
        self,
        project_path: Path,
        total_tasks: int,
        completed_tasks: int,
    ) -> None:
        repository = self._registry_repository()
        try:
            core_update_project_progress(
                project_path,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                repository=repository,
            )
        except ProjectRegistryError:
            # Registry entry may not exist yet (e.g., project not registered)
            return

    def _ensure_registry_backend_ready(self) -> None:
        if self._registry_backend != "sqlite":
            return
        self._migrate_registry_to_sqlite()

    def _migrate_registry_to_sqlite(self) -> None:
        sqlite_path = self._sqlite_registry_path
        if sqlite_path.exists():
            return
        json_path = self._json_registry_path
        if not json_path.exists():
            return
        json_repository = self._registry_repository_factory.build(json_path, "json")
        registry = json_repository.load()
        sqlite_repository = self._registry_repository_factory.build(sqlite_path, "sqlite")
        sqlite_repository.save(registry)

    def _hook_bus(self, context: ProjectContext) -> HookBusPort:
        return self._hook_bus_factory(context)

    def _emit_project_event(
        self,
        context: ProjectContext,
        event: HookEvent,
        payload: ProjectPostInitPayload | ProjectPostForgetPayload,
    ) -> None:
        bus = self._hook_bus(context)
        if not bus.is_enabled():
            return
        bus.emit(event, payload)


def initialise_project(
    project_path: Path | None = None,
    *,
    force: bool = False,
    tasky_dir: Path | None = None,
) -> ProjectContext:
    return _service(tasky_dir).initialise_project(project_path, force=force)


def ensure_project_initialised(project_path: Path | None = None) -> ProjectContext:
    return _service().ensure_project_initialised(project_path)


def is_project_initialised(project_path: Path | None = None) -> bool:
    return _service().is_project_initialised(project_path)


def load_project_config(project_path: Path | None = None) -> ProjectConfig:
    return _service().load_project_config(project_path)


def save_project_config(
    config: ProjectConfig,
    project_path: Path | None = None,
) -> Path:
    return _service().save_project_config(config, project_path)


def get_task_repository(project_path: Path | None = None) -> TaskRepository:
    return _service().get_task_repository(project_path)


def build_task_service(project_path: Path | None = None) -> TaskService:
    return _service().build_task_service(project_path)


def register_project(
    project_path: Path,
    *,
    tasky_dir: Path | None = None,
) -> ProjectRegistryEntry:
    return _service(tasky_dir).register_project(project_path)


def unregister_project(
    project_path: Path,
    *,
    tasky_dir: Path | None = None,
    purge: bool = False,
) -> None:
    _service(tasky_dir).unregister_project(project_path, purge=purge)


def list_registered_projects(
    *,
    tasky_dir: Path | None = None,
    include_missing: bool = False,
) -> Iterable[ProjectRegistryEntry]:
    return _service(tasky_dir).list_registered_projects(include_missing=include_missing)


def prune_missing_projects(
    *,
    tasky_dir: Path | None = None,
) -> list[ProjectRegistryEntry]:
    return _service(tasky_dir).prune_missing_projects()


def get_project_context(project_path: Path | None = None) -> ProjectContext:
    return _service().get_project_context(project_path)


def _service(tasky_dir: Path | None = None) -> ProjectSettingsService:
    return ProjectSettingsService(tasky_dir=tasky_dir)


def _default_hook_bus_factory(context: ProjectContext) -> HookBusPort:
    return load_project_hook_bus(context)


class _ProgressAwareTaskService(TaskService):
    def __init__(
        self,
        *,
        repository: TaskRepository,
        refresh_callback: Callable[[], None],
        task_factory=None,
        tree_builder=None,
        hook_bus: HookBusPort | None = None,
    ) -> None:
        self._refresh_callback = refresh_callback
        super().__init__(
            repository,
            task_factory=task_factory,
            tree_builder=tree_builder,
            hook_bus=hook_bus,
        )

    def _refresh_progress(self) -> None:
        try:
            self._refresh_callback()
        except Exception:
            # Progress refresh is best-effort; loggers can hook via observers if needed.
            return

    def create(self, *args, **kwargs):
        task = super().create(*args, **kwargs)
        self._refresh_progress()
        return task

    def remove(self, *args, **kwargs):
        task = super().remove(*args, **kwargs)
        self._refresh_progress()
        return task

    def replace(self, *args, **kwargs):
        result = super().replace(*args, **kwargs)
        self._refresh_progress()
        return result

    def import_tasks(self, *args, **kwargs):
        tasks = super().import_tasks(*args, **kwargs)
        self._refresh_progress()
        return tasks

    def complete(self, *args, **kwargs):
        task = super().complete(*args, **kwargs)
        self._refresh_progress()
        return task

    def reopen(self, *args, **kwargs):
        task = super().reopen(*args, **kwargs)
        self._refresh_progress()
        return task

    def update(self, *args, **kwargs):
        task = super().update(*args, **kwargs)
        self._refresh_progress()
        return task
