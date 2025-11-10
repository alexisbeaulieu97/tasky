import json
import shutil
from pathlib import Path

import pytest

from tasky_core.projects import (
    ProjectAlreadyInitialisedError,
    ProjectInitialisationError,
    ProjectRegistryEntry,
    ProjectRegistry,
    initialise_project,
    list_registered_projects,
    load_project_config,
    prune_missing_projects,
    register_project,
)
from tasky_core.projects.registry import ProjectRegistryRepository
from tasky_core.projects.ports import ProjectConfigStore, TaskBootstrapper


class _InMemoryRegistryRepository(ProjectRegistryRepository):
    def __init__(self) -> None:
        self.registry = ProjectRegistry()

    def load(self) -> ProjectRegistry:
        return self.registry

    def save(self, registry: ProjectRegistry) -> None:
        self.registry = registry


def _file_store() -> ProjectConfigStore:
    class Store(ProjectConfigStore):
        def read_config(self, context):
            return json.loads(context.config_path.read_text(encoding="utf-8"))

        def write_config(self, context, payload):
            context.metadata_dir.mkdir(parents=True, exist_ok=True)
            context.config_path.write_text(json.dumps(payload), encoding="utf-8")

    return Store()


def _task_bootstrapper() -> TaskBootstrapper:
    class Bootstrap(TaskBootstrapper):
        def initialise_tasks(self, path: Path, *, force: bool) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not force:
                return
            path.write_text(json.dumps({"tasks": []}), encoding="utf-8")

    return Bootstrap()


def test_initialise_project_creates_metadata(tmp_path: Path) -> None:
    project = tmp_path / "workspace"
    context = initialise_project(
        project,
        config_store=_file_store(),
        task_bootstrapper=_task_bootstrapper(),
    )

    assert context.config_path.exists()
    config = load_project_config(project, config_store=_file_store())
    assert config.tasks_file == Path("tasks.json")


def test_register_and_list_projects(tmp_path: Path) -> None:
    project = tmp_path / "workspace"
    repository = _InMemoryRegistryRepository()
    initialise_project(
        project,
        config_store=_file_store(),
        task_bootstrapper=_task_bootstrapper(),
    )

    entry = register_project(project, repository=repository)

    assert isinstance(entry, ProjectRegistryEntry)
    projects = list(list_registered_projects(repository=repository))
    assert len(projects) == 1


def test_initialise_project_prevents_duplicate_without_force(tmp_path: Path) -> None:
    project = tmp_path / "workspace"
    initialise_project(
        project,
        config_store=_file_store(),
        task_bootstrapper=_task_bootstrapper(),
    )

    with pytest.raises(ProjectAlreadyInitialisedError):
        initialise_project(
            project,
            config_store=_file_store(),
            task_bootstrapper=_task_bootstrapper(),
        )


def test_prune_missing_projects(tmp_path: Path) -> None:
    repository = _InMemoryRegistryRepository()
    project = tmp_path / "workspace"
    initialise_project(
        project,
        config_store=_file_store(),
        task_bootstrapper=_task_bootstrapper(),
    )
    register_project(project, repository=repository)
    assert len(list(list_registered_projects(repository=repository))) == 1

    _remove_directory(project)

    removed = prune_missing_projects(repository=repository)
    assert len(removed) == 1
    assert list(list_registered_projects(repository=repository)) == []


def test_load_project_config_raises_for_malformed_json(tmp_path: Path) -> None:
    project = tmp_path / "workspace"
    context = initialise_project(
        project,
        config_store=_file_store(),
        task_bootstrapper=_task_bootstrapper(),
    )
    context.config_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ProjectInitialisationError):
        load_project_config(project, config_store=_file_store())


def _remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
