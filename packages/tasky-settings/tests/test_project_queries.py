from __future__ import annotations

import json
from pathlib import Path

from tasky_models import Task
from tasky_settings.projects import ProjectSettingsService
from tasky_settings.queries import ProjectQueryService


def test_project_query_service_reports_existing_project(tmp_path: Path) -> None:
    tasky_dir = tmp_path / "tasky"
    service = ProjectSettingsService(tasky_dir=tasky_dir)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    service.initialise_project(project_dir)

    query = ProjectQueryService(service)
    overviews = query.list_overviews()

    assert len(overviews) == 1
    overview = overviews[0]
    assert overview.exists is True
    assert overview.progress == (0, 0)


def test_project_query_service_includes_missing_when_requested(tmp_path: Path) -> None:
    tasky_dir = tmp_path / "tasky"
    service = ProjectSettingsService(tasky_dir=tasky_dir)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    service.initialise_project(project_dir)
    # Remove metadata to simulate missing project
    metadata_dir = project_dir / ".tasky"
    for path in metadata_dir.glob("**/*"):
        if path.is_file():
            path.unlink()
    metadata_dir.rmdir()

    query = ProjectQueryService(service)
    overviews = query.list_overviews(include_missing=True)

    assert len(overviews) == 1
    overview = overviews[0]
    assert overview.exists is False
    assert overview.progress is None


def test_project_query_service_refreshes_cache(tmp_path: Path) -> None:
    tasky_dir = tmp_path / "tasky"
    service = ProjectSettingsService(tasky_dir=tasky_dir)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    service.initialise_project(project_dir)

    tasks_path = project_dir / ".tasky" / "tasks.json"
    task = Task.create(name="Cached", details="manually added")
    tasks_path.write_text(json.dumps({"tasks": [task.model_dump(mode="json")]}), encoding="utf-8")

    query = ProjectQueryService(service)
    cached = query.list_overviews()
    assert cached[0].progress == (0, 0)

    refreshed = query.list_overviews(refresh_cache=True)
    assert refreshed[0].progress == (1, 1)
