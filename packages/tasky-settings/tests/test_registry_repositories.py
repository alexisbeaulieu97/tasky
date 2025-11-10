from __future__ import annotations

import json
from pathlib import Path

import pytest

from tasky_core.projects import ProjectRegistry, ProjectRegistryEntry, ProjectRegistryError
from tasky_settings.registry_repositories import (
    JsonProjectRegistryRepository,
    ProjectRegistryRepositoryFactory,
    SQLiteProjectRegistryRepository,
)


def test_json_repository_loads_empty_when_missing(tmp_path: Path) -> None:
    repo = JsonProjectRegistryRepository(tmp_path / "registry.json")

    registry = repo.load()

    assert isinstance(registry, ProjectRegistry)
    assert registry.projects == []


def test_json_repository_raises_for_malformed_payload(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    path.write_text("{invalid", encoding="utf-8")
    repo = JsonProjectRegistryRepository(path)

    with pytest.raises(ProjectRegistryError):
        repo.load()


def test_json_repository_persists_registry(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    repo = JsonProjectRegistryRepository(path)
    registry = ProjectRegistry(
        projects=[ProjectRegistryEntry(path=tmp_path / "project")],
    )

    repo.save(registry)

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["projects"][0]["path"]
    assert "total_tasks" in on_disk["projects"][0]


def test_sqlite_repository_persists_entries(tmp_path: Path) -> None:
    path = tmp_path / "registry.db"
    repo = SQLiteProjectRegistryRepository(path)
    registry = ProjectRegistry(
        projects=[ProjectRegistryEntry(path=tmp_path / "project")],
    )

    repo.save(registry)
    loaded = repo.load()

    assert len(loaded.projects) == 1


def test_repository_factory_selects_backend(tmp_path: Path) -> None:
    factory = ProjectRegistryRepositoryFactory()
    json_repo = factory.build(tmp_path / "registry.json", "json")
    sqlite_repo = factory.build(tmp_path / "registry.db", "sqlite")

    assert isinstance(json_repo, JsonProjectRegistryRepository)
    assert isinstance(sqlite_repo, SQLiteProjectRegistryRepository)
