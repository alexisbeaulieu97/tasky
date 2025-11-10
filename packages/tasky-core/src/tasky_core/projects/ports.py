from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Protocol

if TYPE_CHECKING:
    from .context import ProjectContext


class ProjectConfigReader(Protocol):
    def read_config(self, context: "ProjectContext") -> Mapping[str, Any]: ...


class ProjectConfigWriter(Protocol):
    def write_config(self, context: "ProjectContext", payload: Mapping[str, Any]) -> None: ...


class ProjectConfigStore(ProjectConfigReader, ProjectConfigWriter, Protocol):
    """Combined read/write port for project configuration."""


class TaskBootstrapper(Protocol):
    def initialise_tasks(self, path: Path, *, force: bool) -> None: ...
