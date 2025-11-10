from __future__ import annotations

from pathlib import Path
from typing import Mapping

from tasky_core.projects.ports import ProjectConfigStore, TaskBootstrapper
from tasky_shared.jsonio import atomic_write_json, read_json_document


class FileProjectConfigStore(ProjectConfigStore):
    def read_config(self, context) -> Mapping[str, object]:
        return read_json_document(context.config_path)

    def write_config(self, context, payload: Mapping[str, object]) -> None:
        atomic_write_json(context.config_path, payload)


class FileTaskBootstrapper(TaskBootstrapper):
    def initialise_tasks(self, path: Path, *, force: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            return
        atomic_write_json(path, {"tasks": []})
