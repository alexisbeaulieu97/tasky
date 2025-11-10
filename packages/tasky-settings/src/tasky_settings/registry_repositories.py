from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from tasky_core.projects.persistence import atomic_write_json, load_json_document
from tasky_core.projects.registry import (
    ProjectRegistry,
    ProjectRegistryError,
    ProjectRegistryRepository,
    RegistryBackend,
)
from tasky_storage import SQLiteDocumentStore, StorageDataError


class JsonProjectRegistryRepository(ProjectRegistryRepository):
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> ProjectRegistry:
        try:
            data = load_json_document(self._path, missing_ok=True)
            if not data:
                return ProjectRegistry()
            return ProjectRegistry.model_validate(data)
        except OSError as exc:
            raise ProjectRegistryError(f"Could not read registry at {self._path}.") from exc
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProjectRegistryError(f"Malformed registry at {self._path}.") from exc

    def save(self, registry: ProjectRegistry) -> None:
        payload = registry.model_dump(mode="json")
        try:
            atomic_write_json(self._path, payload)
        except OSError as exc:
            raise ProjectRegistryError(f"Could not write registry at {self._path}.") from exc


class SQLiteProjectRegistryRepository(ProjectRegistryRepository):
    def __init__(
        self,
        database_path: Path,
        *,
        table_name: str = "registry_documents",
        key: str = "projects",
    ) -> None:
        self._store = SQLiteDocumentStore(
            database_path,
            table_name=table_name,
            key=key,
        )

    def load(self) -> ProjectRegistry:
        try:
            document = self._store.load()
        except StorageDataError as exc:
            raise ProjectRegistryError("Could not read registry from SQLite store.") from exc
        if not document:
            return ProjectRegistry()
        try:
            return ProjectRegistry.model_validate(document)
        except ValidationError as exc:
            raise ProjectRegistryError("Malformed registry data in SQLite store.") from exc

    def save(self, registry: ProjectRegistry) -> None:
        payload = registry.model_dump(mode="json")
        try:
            self._store.save(payload)
        except StorageDataError as exc:
            raise ProjectRegistryError("Could not write registry to SQLite store.") from exc


@dataclass(frozen=True)
class ProjectRegistryRepositoryFactory:
    """Builds project registry repositories for the configured backend."""

    def build(
        self,
        path: Path,
        backend: RegistryBackend,
    ) -> ProjectRegistryRepository:
        if backend == "sqlite":
            return SQLiteProjectRegistryRepository(path)
        return JsonProjectRegistryRepository(path)
