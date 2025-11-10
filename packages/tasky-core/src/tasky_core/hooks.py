from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence, Self

from tasky_models import Task


HOOK_MANIFEST_FILENAME = "hook.json"


class HookError(Exception):
    """Base error for hook orchestration."""


class HookConfigurationError(HookError):
    """Raised when hook manifests are missing or malformed."""


class HookExecutionError(HookError):
    """Raised when a hook command fails (non-zero exit, timeout, invalid output)."""


class HookEvent(str, Enum):
    TASK_PRE_ADD = "task.pre_add"
    TASK_POST_ADD = "task.post_add"
    TASK_PRE_REMOVE = "task.pre_remove"
    TASK_POST_REMOVE = "task.post_remove"
    TASK_PRE_IMPORT = "task.pre_import"
    TASK_POST_IMPORT = "task.post_import"
    TASK_PRE_COMPLETE = "task.pre_complete"
    TASK_POST_COMPLETE = "task.post_complete"
    TASK_PRE_REOPEN = "task.pre_reopen"
    TASK_POST_REOPEN = "task.post_reopen"
    TASK_PRE_UPDATE = "task.pre_update"
    TASK_POST_UPDATE = "task.post_update"
    PROJECT_POST_INIT = "project.post_init"
    PROJECT_POST_FORGET = "project.post_forget"


@dataclass(frozen=True)
class HookDefinition:
    id: str
    event: HookEvent
    command: tuple[str, ...]
    timeout: float | None = None
    continue_on_error: bool = False


@dataclass(frozen=True)
class HookManifest:
    version: int
    hooks: tuple[HookDefinition, ...]

    def hooks_for(self, event: HookEvent) -> Sequence[HookDefinition]:
        for hook in self.hooks:
            if hook.event == event:
                yield hook


@dataclass(frozen=True)
class HookPayload:
    event: HookEvent
    project_path: Path
    data: Mapping[str, Any]

    def with_data(self, data: Mapping[str, Any]) -> HookPayload:
        return HookPayload(event=self.event, project_path=self.project_path, data=data)

    def to_json(self) -> str:
        serialisable = {
            "event": self.event.value,
            "project_path": str(self.project_path),
            **self.data,
        }
        return json.dumps(serialisable, default=_json_default)


@dataclass(frozen=True)
class HookResult:
    hook: HookDefinition
    payload: HookPayload | None
    return_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class HookDispatchResult:
    payload: HookPayload
    results: Sequence[HookResult] = field(default_factory=tuple)


class HookRunner(Protocol):
    """Port describing hook runner behaviour."""

    def is_enabled(self) -> bool: ...

    def run(
        self,
        event: HookEvent,
        payload: "PayloadInput",
    ) -> HookDispatchResult: ...


class HookBusPort(Protocol):
    """Higher-level hook dispatcher supporting pre/post workflows."""

    def is_enabled(self) -> bool: ...

    def mutate(self, event: HookEvent, payload: HookPayloadModel) -> HookPayloadModel: ...

    def emit(self, event: HookEvent, payload: PayloadInput | None = None) -> None: ...


class NullHookBus(HookBusPort):
    """Fallback hook bus that performs no work."""

    def is_enabled(self) -> bool:
        return False

    def mutate(self, event: HookEvent, payload: HookPayloadModel) -> HookPayloadModel:
        return payload

    def emit(self, event: HookEvent, payload: PayloadInput | None = None) -> None:
        return None


class HookPayloadModel(ABC):
    """Typed payload contract for hook events."""

    @classmethod
    @abstractmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        """Construct a payload from hook output."""

    @abstractmethod
    def to_mapping(self) -> Mapping[str, Any]:
        """Convert payload data to a serialisable mapping."""


PayloadInput = HookPayloadModel | Mapping[str, Any]


def _coerce_payload_mapping(payload: PayloadInput) -> dict[str, Any]:
    if isinstance(payload, HookPayloadModel):
        mapping = payload.to_mapping()
    else:
        mapping = payload
    if not isinstance(mapping, Mapping):
        raise HookExecutionError("Hook payloads must be mapping types.")
    return dict(mapping)


@dataclass(frozen=True)
class TaskPreAddPayload(HookPayloadModel):
    name: str
    details: str
    parent_id: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        name = _require_str(data, "name", event=HookEvent.TASK_PRE_ADD.value)
        details = _require_str(data, "details", event=HookEvent.TASK_PRE_ADD.value)
        parent_value = data.get("parent_id")
        parent_id = None if parent_value is None else str(parent_value)
        return cls(name=name, details=details, parent_id=parent_id)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"name": self.name, "details": self.details, "parent_id": self.parent_id}


@dataclass(frozen=True)
class TaskPostAddPayload(HookPayloadModel):
    task: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task = _require_mapping(data, "task", event=HookEvent.TASK_POST_ADD.value)
        return cls(task=dict(task))

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task": dict(self.task)}


@dataclass(frozen=True)
class TaskPreRemovePayload(HookPayloadModel):
    task_id: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task_id = _require_str(data, "task_id", event=HookEvent.TASK_PRE_REMOVE.value)
        return cls(task_id=task_id)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task_id": self.task_id}


@dataclass(frozen=True)
class TaskPostRemovePayload(HookPayloadModel):
    task: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task = _require_mapping(data, "task", event=HookEvent.TASK_POST_REMOVE.value)
        return cls(task=dict(task))

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task": dict(self.task)}


@dataclass(frozen=True)
class TaskPreCompletePayload(HookPayloadModel):
    task_id: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task_id = _require_str(data, "task_id", event=HookEvent.TASK_PRE_COMPLETE.value)
        return cls(task_id=task_id)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task_id": self.task_id}


@dataclass(frozen=True)
class TaskPostCompletePayload(HookPayloadModel):
    task: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task = _require_mapping(data, "task", event=HookEvent.TASK_POST_COMPLETE.value)
        return cls(task=dict(task))

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task": dict(self.task)}


@dataclass(frozen=True)
class TaskPreReopenPayload(HookPayloadModel):
    task_id: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task_id = _require_str(data, "task_id", event=HookEvent.TASK_PRE_REOPEN.value)
        return cls(task_id=task_id)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task_id": self.task_id}


@dataclass(frozen=True)
class TaskPostReopenPayload(HookPayloadModel):
    task: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task = _require_mapping(data, "task", event=HookEvent.TASK_POST_REOPEN.value)
        return cls(task=dict(task))

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task": dict(self.task)}


@dataclass(frozen=True)
class TaskPreUpdatePayload(HookPayloadModel):
    task_id: str
    name: str | None = None
    details: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task_id = _require_str(data, "task_id", event=HookEvent.TASK_PRE_UPDATE.value)
        name = data.get("name")
        details = data.get("details")
        return cls(
            task_id=task_id,
            name=str(name) if name is not None else None,
            details=str(details) if details is not None else None,
        )

    def to_mapping(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {"task_id": self.task_id}
        if self.name is not None:
            payload["name"] = self.name
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class TaskPostUpdatePayload(HookPayloadModel):
    task: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        task = _require_mapping(data, "task", event=HookEvent.TASK_POST_UPDATE.value)
        return cls(task=dict(task))

    def to_mapping(self) -> Mapping[str, Any]:
        return {"task": dict(self.task)}


@dataclass(frozen=True)
class TaskPreImportPayload(HookPayloadModel):
    strategy: str
    tasks: Sequence[Mapping[str, Any]]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        strategy = _require_str(data, "strategy", event=HookEvent.TASK_PRE_IMPORT.value)
        tasks = _require_task_list(data, "tasks")
        return cls(strategy=strategy, tasks=tuple(dict(task) for task in tasks))

    def to_mapping(self) -> Mapping[str, Any]:
        return {
            "strategy": self.strategy,
            "tasks": [dict(task) for task in self.tasks],
        }


@dataclass(frozen=True)
class TaskPostImportPayload(HookPayloadModel):
    strategy: str
    imported: int

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        strategy = _require_str(data, "strategy", event=HookEvent.TASK_POST_IMPORT.value)
        imported = _require_int(data, "imported", event=HookEvent.TASK_POST_IMPORT.value)
        return cls(strategy=strategy, imported=imported)

    def to_mapping(self) -> Mapping[str, Any]:
        return {"strategy": self.strategy, "imported": self.imported}


@dataclass(frozen=True)
class ProjectPostInitPayload(HookPayloadModel):
    reinitialised: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            reinitialised=_require_bool(
                data,
                "reinitialised",
                event=HookEvent.PROJECT_POST_INIT.value,
            )
        )

    def to_mapping(self) -> Mapping[str, Any]:
        return {"reinitialised": self.reinitialised}


@dataclass(frozen=True)
class ProjectPostForgetPayload(HookPayloadModel):
    purged: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            purged=_require_bool(
                data,
                "purged",
                event=HookEvent.PROJECT_POST_FORGET.value,
            )
        )

    def to_mapping(self) -> Mapping[str, Any]:
        return {"purged": self.purged}


def _require_str(data: Mapping[str, Any], key: str, *, event: str) -> str:
    if key not in data:
        raise HookExecutionError(f"Hook payload for '{event}' must include '{key}'.")
    value = data[key]
    if value is None:
        raise HookExecutionError(f"Hook payload field '{key}' cannot be null.")
    return str(value)


def _require_int(data: Mapping[str, Any], key: str, *, event: str) -> int:
    if key not in data:
        raise HookExecutionError(f"Hook payload for '{event}' must include '{key}'.")
    value = data[key]
    if isinstance(value, bool):
        raise HookExecutionError(f"Hook payload field '{key}' must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, (float,)):
        return int(value)
    raise HookExecutionError(f"Hook payload field '{key}' must be an integer.")


def _require_bool(data: Mapping[str, Any], key: str, *, event: str) -> bool:
    if key not in data:
        raise HookExecutionError(f"Hook payload for '{event}' must include '{key}'.")
    value = data[key]
    if isinstance(value, bool):
        return value
    raise HookExecutionError(f"Hook payload field '{key}' must be a boolean.")


def _require_mapping(data: Mapping[str, Any], key: str, *, event: str) -> Mapping[str, Any]:
    if key not in data:
        raise HookExecutionError(f"Hook payload for '{event}' must include '{key}'.")
    value = data[key]
    if not isinstance(value, Mapping):
        raise HookExecutionError(f"Hook payload field '{key}' must be an object.")
    return value


def _require_task_list(data: Mapping[str, Any], key: str) -> Sequence[Mapping[str, Any]]:
    if key not in data:
        raise HookExecutionError("Hook payload for 'task.pre_import' must include 'tasks'.")
    value = data[key]
    if not isinstance(value, list):
        raise HookExecutionError("Hook payload field 'tasks' must be a list of objects.")
    tasks: list[Mapping[str, Any]] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, Mapping):
            raise HookExecutionError(
                f"Hook payload 'tasks' entry #{index} must be a JSON object."
            )
        tasks.append(entry)
    return tasks
def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Task):
        return value.model_dump(mode="json")
    if hasattr(value, "model_dump"):
        return value.model_dump()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serialisable.")
