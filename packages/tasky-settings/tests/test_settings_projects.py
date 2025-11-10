from __future__ import annotations

import json
from pathlib import Path

import pytest

from tasky_settings import (
    ProjectAlreadyInitialisedError,
    ProjectInitialisationError,
    ProjectSettingsError,
    ProjectSettingsService,
    TaskRepositoryFactory,
    ensure_project_initialised,
    get_project_context,
    get_task_repository,
    initialise_project,
    list_registered_projects,
    unregister_project,
)
from tasky_settings.projects import (
    PROJECT_CONFIG_FILENAME,
    REGISTRY_FILENAME,
    REGISTRY_SQLITE_FILENAME,
)
from tasky_storage import JsonTaskRepository
from tasky_core.projects import ProjectConfig, ProjectContext
from tasky_models import Task


def test_initialise_project_creates_files_and_registry(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )

    config_path = project_dir / ".tasky" / PROJECT_CONFIG_FILENAME
    assert config_path.exists()
    on_disk = json.loads(config_path.read_text())
    assert on_disk["tasks_file"] == "tasks.json"

    tasks_path = project_dir / ".tasky" / "tasks.json"
    assert tasks_path.exists()
    assert json.loads(tasks_path.read_text()) == {"tasks": []}
    context = get_project_context(project_dir)
    assert context.tasks_path == tasks_path

    registry_path = tasky_root / REGISTRY_FILENAME
    assert registry_path.exists()
    entries = list(list_registered_projects(tasky_dir=tasky_root, include_missing=True))
    assert len(entries) == 1
    assert Path(entries[0].path) == project_dir.resolve()


def test_initialise_without_force_raises(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )

    with pytest.raises(ProjectAlreadyInitialisedError):
        initialise_project(
            project_path=project_dir,
            tasky_dir=tasky_root,
        )


def test_ensure_project_initialised(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    with pytest.raises(ProjectInitialisationError):
        ensure_project_initialised(project_dir)

    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )

    context = ensure_project_initialised(project_dir)
    assert context.project_path == project_dir
    assert context.config_path.exists()


def test_get_task_repository_reads_empty_document(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )

    repo = get_task_repository(project_dir)
    assert repo.list_tasks() == []


def test_get_task_repository_supports_sqlite_backend(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )
    config_path = project_dir / ".tasky" / PROJECT_CONFIG_FILENAME
    payload = json.loads(config_path.read_text())
    payload["tasks_file"] = "tasks.sqlite"
    config_path.write_text(json.dumps(payload))

    repo = get_task_repository(project_dir)
    assert repo.list_tasks() == []
    sqlite_path = project_dir / ".tasky" / "tasks.sqlite"
    assert sqlite_path.exists()


def test_unregister_project_removes_entry(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    initialise_project(
        project_path=project_dir,
        tasky_dir=tasky_root,
    )

    unregister_project(project_dir, tasky_dir=tasky_root)
    entries = list(list_registered_projects(tasky_dir=tasky_root, include_missing=True))
    assert entries == []


def test_project_settings_service_uses_sqlite_registry_backend(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    service = ProjectSettingsService(tasky_dir=tasky_root, registry_backend="sqlite")
    service.initialise_project(project_dir)

    registry_path = tasky_root / REGISTRY_SQLITE_FILENAME
    assert registry_path.exists()
    entries = list(service.list_registered_projects(include_missing=True))
    assert len(entries) == 1


def test_project_settings_service_migrates_json_registry(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    initialise_project(project_path=project_dir, tasky_dir=tasky_root)
    json_registry = tasky_root / REGISTRY_FILENAME
    assert json_registry.exists()

    service = ProjectSettingsService(tasky_dir=tasky_root, registry_backend="sqlite")
    entries = list(service.list_registered_projects(include_missing=True))

    sqlite_registry = tasky_root / REGISTRY_SQLITE_FILENAME
    assert sqlite_registry.exists()
    assert len(entries) == 1


def test_project_settings_service_accepts_custom_repository_factory(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    initialise_project(project_path=project_dir, tasky_dir=tasky_root)

    class RecordingFactory(TaskRepositoryFactory):
        def __init__(self) -> None:
            self.calls: list[tuple] = []

        def build(
            self,
            context: ProjectContext,
            config: ProjectConfig,
        ) -> JsonTaskRepository:
            self.calls.append((context, config))
            return super().build(context, config)

    factory = RecordingFactory()
    service = ProjectSettingsService(
        tasky_dir=tasky_root,
        repository_factory=factory,
    )

    repo = service.get_task_repository(project_dir)

    assert len(factory.calls) == 1
    assert repo.list_tasks() == []


def test_update_project_config_to_sqlite_migrates_tasks(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    service = ProjectSettingsService(tasky_dir=tasky_root)
    service.initialise_project(project_dir)
    repo = service.get_task_repository(project_dir)
    repo.upsert_task(Task.create(name="Example", details="Details"))

    entries = list(service.list_registered_projects(include_missing=True))
    before_updated_at = entries[0].updated_at

    updated = service.update_project_config(
        project_path=project_dir,
        updates={"tasks_file": "tasks.sqlite"},
        force=True,
    )

    assert updated.tasks_file.name == "tasks.sqlite"
    new_repo = service.get_task_repository(project_dir)
    tasks = new_repo.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "Example"

    refreshed_entries = list(service.list_registered_projects(include_missing=True))
    assert refreshed_entries[0].updated_at >= before_updated_at


def test_update_project_config_requires_force_when_target_exists(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    service = ProjectSettingsService(tasky_dir=tasky_root)
    service.initialise_project(project_dir)

    custom_path = project_dir / ".tasky" / "custom.json"
    custom_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ProjectSettingsError):
        service.update_project_config(
            project_path=project_dir,
            updates={"tasks_file": "custom.json"},
            force=False,
        )


def test_update_project_config_rejects_unknown_keys(tmp_path: Path) -> None:
    tasky_root = tmp_path / "tasky-root"
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    service = ProjectSettingsService(tasky_dir=tasky_root)
    service.initialise_project(project_dir)

    with pytest.raises(ProjectSettingsError):
        service.update_project_config(
            project_path=project_dir,
            updates={"unknown": "value"},
        )
