from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from tasky_core.hooks import (
    HOOK_MANIFEST_FILENAME,
    HookBusPort,
    HookConfigurationError,
    HookDefinition,
    HookDispatchResult,
    HookEvent,
    HookExecutionError,
    HookManifest,
    HookPayload,
    HookPayloadModel,
    HookResult,
    HookRunner,
    NullHookBus,
    PayloadInput,
    _coerce_payload_mapping,
)
from tasky_core.projects.context import ProjectContext, get_project_context

_HOOK_BUS_CACHE_LOCK = RLock()


@dataclass(frozen=True)
class _HookBusCacheEntry:
    signature: tuple[Any, ...]
    bus: HookBusPort


_HOOK_BUS_CACHE: dict[Path, _HookBusCacheEntry] = {}


class ProjectHookRunner(HookRunner):
    """Orchestrates hook discovery + execution for a project."""

    def __init__(
        self,
        *,
        project_path: Path,
        hooks_dir: Path,
        manifest: HookManifest | None,
    ) -> None:
        self._project_path = project_path
        self._hooks_dir = hooks_dir
        self._manifest = manifest

    def is_enabled(self) -> bool:
        return bool(self._manifest and self._manifest.hooks)

    def run(
        self,
        event: HookEvent,
        payload: PayloadInput,
    ) -> HookDispatchResult:
        payload_mapping = _coerce_payload_mapping(payload)
        if not self.is_enabled():
            return HookDispatchResult(
                payload=HookPayload(
                    event=event,
                    project_path=self._project_path,
                    data=payload_mapping,
                ),
                results=(),
            )

        hooks = list(self._manifest.hooks_for(event))  # type: ignore[union-attr]
        if not hooks:
            return HookDispatchResult(
                payload=HookPayload(
                    event=event,
                    project_path=self._project_path,
                    data=payload_mapping,
                ),
                results=(),
            )

        self._hooks_dir.mkdir(parents=True, exist_ok=True)
        current_payload = HookPayload(
            event=event,
            project_path=self._project_path,
            data=payload_mapping,
        )
        results: list[HookResult] = []
        for definition in hooks:
            result = self._execute_hook(definition, current_payload)
            results.append(result)
            if result.payload is not None:
                current_payload = result.payload
        return HookDispatchResult(payload=current_payload, results=tuple(results))

    def _execute_hook(
        self,
        definition: HookDefinition,
        payload: HookPayload,
    ) -> HookResult:
        completed = _run_hook_process(
            definition=definition,
            serialized_payload=payload.to_json(),
            hooks_dir=self._hooks_dir,
            project_path=self._project_path,
        )
        payload_update = _parse_hook_stdout(
            definition=definition,
            stdout=completed.stdout.strip(),
            base_payload=payload,
        )
        _raise_for_nonzero_exit(definition, completed)
        return HookResult(
            hook=definition,
            payload=payload_update,
            return_code=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr,
        )


def load_project_hook_runner(
    target: ProjectContext | Path | None = None,
) -> ProjectHookRunner:
    context = target if isinstance(target, ProjectContext) else get_project_context(target)
    hooks_dir = context.metadata_dir / "hooks"
    manifest = _load_manifest(hooks_dir)
    return ProjectHookRunner(
        project_path=context.project_path,
        hooks_dir=hooks_dir,
        manifest=manifest,
    )


class RunnerHookBus(HookBusPort):
    """Hook bus that delegates to a HookRunner."""

    def __init__(self, runner: HookRunner) -> None:
        self._runner = runner

    def is_enabled(self) -> bool:
        return self._runner.is_enabled()

    def mutate(self, event: HookEvent, payload: HookPayloadModel) -> HookPayloadModel:
        dispatch = self._runner.run(event, payload)
        payload_type = type(payload)
        return payload_type.from_mapping(dispatch.payload.data)

    def emit(self, event: HookEvent, payload: PayloadInput | None = None) -> None:
        self._runner.run(event, payload or {})


def load_project_hook_bus(
    target: ProjectContext | Path | None = None,
) -> HookBusPort:
    context = target if isinstance(target, ProjectContext) else get_project_context(target)
    hooks_dir = context.metadata_dir / "hooks"
    signature = _hook_signature(hooks_dir)
    cache_key = context.project_path
    with _HOOK_BUS_CACHE_LOCK:
        cached = _HOOK_BUS_CACHE.get(cache_key)
        if cached and cached.signature == signature:
            return cached.bus
    runner = load_project_hook_runner(context)
    bus: HookBusPort = RunnerHookBus(runner) if runner.is_enabled() else NullHookBus()
    with _HOOK_BUS_CACHE_LOCK:
        _HOOK_BUS_CACHE[cache_key] = _HookBusCacheEntry(signature=signature, bus=bus)
    return bus


def clear_hook_bus_cache() -> None:
    """Reset the in-memory hook bus cache (useful in tests)."""
    with _HOOK_BUS_CACHE_LOCK:
        _HOOK_BUS_CACHE.clear()


def _load_manifest(hooks_dir: Path) -> HookManifest | None:
    manifest_path = hooks_dir / HOOK_MANIFEST_FILENAME
    if not manifest_path.exists():
        return None
    data = _read_manifest_data(manifest_path)
    return _build_manifest_from_data(data)


def _hook_signature(hooks_dir: Path) -> tuple[Any, ...]:
    if not hooks_dir.exists():
        return ("missing-hooks-dir",)
    files_signature = _collect_hook_files_signature(hooks_dir)
    if files_signature is None:
        return ("missing-hooks-dir",)
    return ("hooks", files_signature)


def _collect_hook_files_signature(
    hooks_dir: Path,
) -> tuple[tuple[str, int, int], ...] | None:
    entries: list[tuple[str, int, int]] = []
    try:
        for path in hooks_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            rel = path.relative_to(hooks_dir).as_posix()
            entries.append((rel, stat.st_mtime_ns, stat.st_size))
    except OSError:
        return None
    entries.sort()
    return tuple(entries)


def _parse_hook_definition(raw_hook: Any, index: int) -> HookDefinition:
    entry = _ensure_dict(raw_hook, index)
    hook_id = _parse_hook_id(entry)
    hook_event = _parse_hook_event(entry, hook_id)
    command = _parse_hook_command(entry, hook_id)
    timeout = _parse_hook_timeout(entry, hook_id)
    continue_on_error = bool(entry.get("continue_on_error", False))
    return HookDefinition(
        id=hook_id,
        event=hook_event,
        command=command,
        timeout=timeout,
        continue_on_error=continue_on_error,
    )


def _build_environment(
    *,
    hook: HookDefinition,
    project_path: Path,
    hooks_dir: Path,
) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "TASKY_HOOK_EVENT": hook.event.value,
            "TASKY_HOOK_ID": hook.id,
            "TASKY_PROJECT_ROOT": str(project_path),
            "TASKY_HOOKS_DIR": str(hooks_dir),
        }
    )
    return env


def _run_hook_process(
    *,
    definition: HookDefinition,
    serialized_payload: str,
    hooks_dir: Path,
    project_path: Path,
) -> subprocess.CompletedProcess[str]:
    env = _build_environment(
        hook=definition,
        project_path=project_path,
        hooks_dir=hooks_dir,
    )
    try:
        return subprocess.run(
            definition.command,
            input=serialized_payload,
            capture_output=True,
            cwd=hooks_dir,
            text=True,
            timeout=definition.timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise HookExecutionError(
            f"Hook '{definition.id}' timed out after {definition.timeout or 0}s."
        ) from exc
    except OSError as exc:
        raise HookExecutionError(
            f"Hook '{definition.id}' failed to start: {exc}"
        ) from exc


def _parse_hook_stdout(
    *,
    definition: HookDefinition,
    stdout: str,
    base_payload: HookPayload,
) -> HookPayload | None:
    if not stdout:
        return None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise HookExecutionError(
            f"Hook '{definition.id}' produced invalid JSON output."
        ) from exc
    if not isinstance(parsed, dict):
        raise HookExecutionError(
            f"Hook '{definition.id}' returned a non-object payload."
        )
    return base_payload.with_data(parsed)


def _raise_for_nonzero_exit(
    definition: HookDefinition,
    completed: subprocess.CompletedProcess[str],
) -> None:
    if completed.returncode != 0 and not definition.continue_on_error:
        raise HookExecutionError(
            f"Hook '{definition.id}' exited with code {completed.returncode}."
        )


def _read_manifest_data(path: Path) -> Any:
    try:
        raw_text = path.read_text(encoding="utf-8")
        return json.loads(raw_text)
    except OSError as exc:
        raise HookConfigurationError("Could not read project hook manifest.") from exc
    except json.JSONDecodeError as exc:
        raise HookConfigurationError("Hook manifest is not valid JSON.") from exc


def _build_manifest_from_data(data: Any) -> HookManifest:
    if not isinstance(data, dict):
        raise HookConfigurationError("Hook manifest must be a JSON object.")
    version = data.get("version")
    if version != 1:
        raise HookConfigurationError("Unsupported hook manifest version.")
    hooks_payload = data.get("hooks", [])
    if not isinstance(hooks_payload, list):
        raise HookConfigurationError("'hooks' must be a list.")
    hooks = [
        _parse_hook_definition(entry, index)
        for index, entry in enumerate(hooks_payload)
    ]
    return HookManifest(version=version, hooks=tuple(hooks))


def _ensure_dict(raw_hook: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw_hook, dict):
        raise HookConfigurationError(f"Hook entry #{index} must be an object.")
    return raw_hook


def _parse_hook_id(entry: dict[str, Any]) -> str:
    hook_id = entry.get("id")
    if not hook_id or not isinstance(hook_id, str):
        raise HookConfigurationError("Hook entries require a string 'id'.")
    return hook_id


def _parse_hook_event(entry: dict[str, Any], hook_id: str) -> HookEvent:
    event = entry.get("event")
    if not event or not isinstance(event, str):
        raise HookConfigurationError(f"Hook '{hook_id}' must define an event name.")
    try:
        return HookEvent(event)
    except ValueError as exc:
        raise HookConfigurationError(
            f"Hook '{hook_id}' references an unknown event '{event}'."
        ) from exc


def _parse_hook_command(entry: dict[str, Any], hook_id: str) -> tuple[str, ...]:
    command = entry.get("command")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        raise HookConfigurationError(
            f"Hook '{hook_id}' must define 'command' as a non-empty array of strings."
        )
    return tuple(command)


def _parse_hook_timeout(entry: dict[str, Any], hook_id: str) -> float | None:
    timeout = entry.get("timeout")
    if timeout is None:
        return None
    if not isinstance(timeout, (int, float)):
        raise HookConfigurationError(f"Hook '{hook_id}' timeout must be numeric.")
    return float(timeout)
