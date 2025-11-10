from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from tasky_core.hooks import (
    HookConfigurationError,
    HookEvent,
    HookExecutionError,
    TaskPreAddPayload,
)
from tasky_core.projects.context import get_project_context
from tasky_storage import (
    clear_hook_bus_cache,
    load_project_hook_bus,
    load_project_hook_runner,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_hook_bus_cache()


def test_load_manifest_returns_none_when_missing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    context = get_project_context(project)

    runner = load_project_hook_runner(context)

    assert runner.is_enabled() is False


def test_load_project_hook_bus_returns_null_when_no_hooks(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    context = get_project_context(project)

    bus = load_project_hook_bus(context)

    assert bus.is_enabled() is False


def test_hook_runner_applies_payload_updates(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "normalize",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "normalize.py"],
            }
        ],
        scripts={
            "normalize.py": """
import json, sys
payload = json.load(sys.stdin)
payload["name"] = payload["name"].upper()
json.dump(payload, sys.stdout)
""",
        },
    )

    dispatch = load_project_hook_runner(context).run(
        HookEvent.TASK_PRE_ADD,
        TaskPreAddPayload(name="demo", details="body", parent_id=None),
    )

    assert dispatch.payload.data["name"] == "DEMO"


def test_hook_runner_respects_continue_on_error(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "optional",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "fail.py"],
                "continue_on_error": True,
            }
        ],
        scripts={"fail.py": "import sys; sys.exit(2)\n"},
    )

    dispatch = load_project_hook_runner(context).run(
        HookEvent.TASK_PRE_ADD,
        TaskPreAddPayload(name="demo", details="body", parent_id=None),
    )

    assert dispatch.payload.data["name"] == "demo"


def test_hook_runner_raises_on_error_when_not_continue(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "required",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "fail.py"],
            }
        ],
        scripts={"fail.py": "import sys; sys.exit(3)\n"},
    )

    with pytest.raises(HookExecutionError):
        load_project_hook_runner(context).run(
            HookEvent.TASK_PRE_ADD,
            TaskPreAddPayload(name="demo", details="body", parent_id=None),
        )


def test_hook_bus_wraps_runner(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "normalize",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "normalize.py"],
            }
        ],
        scripts={
            "normalize.py": """
import json, sys
payload = json.load(sys.stdin)
payload["name"] = payload["name"].upper()
json.dump(payload, sys.stdout)
""",
        },
    )
    bus = load_project_hook_bus(context)
    assert bus.is_enabled() is True

    mutated = bus.mutate(
        HookEvent.TASK_PRE_ADD,
        TaskPreAddPayload(name="demo", details="body"),
    )

    assert mutated.name == "DEMO"
    # emit should no-op when no hooks target the event
    bus.emit(HookEvent.TASK_POST_ADD, {"task": {"name": "demo"}})


def test_hook_bus_cache_reuses_instance_until_manifest_changes(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "normalize",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "normalize.py"],
            }
        ],
        scripts={
            "normalize.py": """
import json, sys
payload = json.load(sys.stdin)
json.dump(payload, sys.stdout)
""",
        },
    )
    bus_one = load_project_hook_bus(context)
    bus_two = load_project_hook_bus(context)
    assert bus_one is bus_two

    manifest_path = context.metadata_dir / "hooks" / "hook.json"
    time.sleep(0.01)
    manifest = {
        "version": 1,
        "hooks": [
            {
                "id": "normalize",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "normalize.py"],
            },
            {
                "id": "noop",
                "event": HookEvent.TASK_POST_ADD.value,
                "command": [sys.executable, "normalize.py"],
            },
        ],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    bus_three = load_project_hook_bus(context)
    assert bus_three is not bus_one


def test_hook_bus_cache_invalidates_when_scripts_change(tmp_path: Path) -> None:
    context = _prepare_project_with_hooks(
        tmp_path,
        hooks=[
            {
                "id": "normalize",
                "event": HookEvent.TASK_PRE_ADD.value,
                "command": [sys.executable, "normalize.py"],
            }
        ],
        scripts={
            "normalize.py": """
import json, sys
payload = json.load(sys.stdin)
json.dump(payload, sys.stdout)
""",
        },
    )
    script_path = context.metadata_dir / "hooks" / "normalize.py"
    bus_one = load_project_hook_bus(context)
    time.sleep(0.01)
    script_path.write_text(
        """
import json, sys
payload = json.load(sys.stdin)
payload["name"] = payload.get("name", "")
json.dump(payload, sys.stdout)
""",
        encoding="utf-8",
    )
    bus_two = load_project_hook_bus(context)
    assert bus_two is not bus_one


def test_invalid_manifest_raises(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".tasky" / "hooks").mkdir(parents=True)
    manifest_path = project / ".tasky" / "hooks" / "hook.json"
    manifest_path.write_text(json.dumps({"version": 99, "hooks": []}), encoding="utf-8")

    with pytest.raises(HookConfigurationError):
        load_project_hook_runner(project)


def _prepare_project_with_hooks(
    tmp_path: Path,
    *,
    hooks: list[dict[str, object]],
    scripts: dict[str, str],
):
    project = tmp_path / "project"
    hooks_dir = project / ".tasky" / "hooks"
    hooks_dir.mkdir(parents=True)
    for name, content in scripts.items():
        script_path = hooks_dir / name
        script_path.write_text(content.lstrip(), encoding="utf-8")
        script_path.chmod(0o755)
    manifest = {"version": 1, "hooks": hooks}
    (hooks_dir / "hook.json").write_text(json.dumps(manifest), encoding="utf-8")
    context = get_project_context(project)
    return context
