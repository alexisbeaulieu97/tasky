from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from tasky_cli import app as cli_app

runner = CliRunner()


def test_project_init_and_task_flow(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()

    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli_app, ["project", "init"])
    assert result.exit_code == 0
    assert (project_dir / ".tasky" / "config.json").exists()

    add = runner.invoke(
        cli_app,
        [
            "task",
            "add",
            "--name",
            "Demo",
            "--details",
            "Write integration test",
        ],
    )
    assert add.exit_code == 0

    tasks_path = project_dir / ".tasky" / "tasks.json"
    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    task_id = payload["tasks"][0]["task_id"]

    complete = runner.invoke(cli_app, ["task", "complete", task_id])
    assert complete.exit_code == 0

    reopen = runner.invoke(cli_app, ["task", "reopen", task_id])
    assert reopen.exit_code == 0

    update = runner.invoke(
        cli_app,
        [
            "task",
            "update",
            task_id,
            "--details",
            "Updated via CLI",
        ],
    )
    assert update.exit_code == 0

    list_res = runner.invoke(cli_app, ["task", "list"])
    assert "Demo" in list_res.stdout
    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    assert payload["tasks"][0]["details"] == "Updated via CLI"

    list_projects = runner.invoke(cli_app, ["project", "list", "--refresh-progress"])
    assert list_projects.exit_code == 0
    assert "0/1" in list_projects.stdout


def test_task_hooks_can_modify_add_payload(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli_app, ["project", "init"])
    assert result.exit_code == 0

    hooks_dir = project_dir / ".tasky" / "hooks"
    hooks_dir.mkdir(parents=True)
    _write_hook_scripts(
        hooks_dir,
        {
            "normalize.py": """
import json, sys
payload = json.load(sys.stdin)
payload["name"] = payload["name"].upper()
json.dump(payload, sys.stdout)
""",
            "post.py": """
import json, os, sys
from pathlib import Path
payload = json.load(sys.stdin)
log_path = Path(os.environ["TASKY_HOOKS_DIR"]) / "post.log"
log_path.write_text(json.dumps(payload), encoding="utf-8")
""",
        },
    )
    manifest = {
        "version": 1,
        "hooks": [
            {
                "id": "normalize",
                "event": "task.pre_add",
                "command": [sys.executable, "normalize.py"],
            },
            {
                "id": "post-log",
                "event": "task.post_add",
                "command": [sys.executable, "post.py"],
                "continue_on_error": True,
            },
        ],
    }
    (hooks_dir / "hook.json").write_text(json.dumps(manifest), encoding="utf-8")

    add = runner.invoke(
        cli_app,
        [
            "task",
            "add",
            "--name",
            "demo",
            "--details",
            "hooked",
        ],
    )
    assert add.exit_code == 0

    list_res = runner.invoke(cli_app, ["task", "list"])
    assert "DEMO" in list_res.stdout
    assert (hooks_dir / "post.log").exists()


def test_import_hook_filters_tasks(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli_app, ["project", "init"])
    assert result.exit_code == 0

    hooks_dir = project_dir / ".tasky" / "hooks"
    hooks_dir.mkdir(parents=True)
    _write_hook_scripts(
        hooks_dir,
        {
            "filter.py": """
import json, sys
payload = json.load(sys.stdin)
payload["tasks"] = [
    task for task in payload["tasks"]
    if task["name"].startswith("Keep")
]
json.dump(payload, sys.stdout)
""",
        },
    )
    manifest = {
        "version": 1,
        "hooks": [
            {
                "id": "filter",
                "event": "task.pre_import",
                "command": [sys.executable, "filter.py"],
            }
        ],
    }
    (hooks_dir / "hook.json").write_text(json.dumps(manifest), encoding="utf-8")

    import_file = project_dir / "tasks.json"
    import_file.write_text(
        json.dumps(
            [
                {"name": "Keep this", "details": "one"},
                {"name": "Drop this", "details": "two"},
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        [
            "task",
            "import",
            "--file",
            str(import_file),
        ],
    )
    assert result.exit_code == 0

    list_res = runner.invoke(cli_app, ["task", "list"])
    assert "Keep this" in list_res.stdout
    assert "Drop this" not in list_res.stdout


def test_project_hooks_scaffold_creates_samples(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)

    result = runner.invoke(cli_app, ["project", "hooks", "scaffold"])
    assert result.exit_code == 0

    hooks_dir = project_dir / ".tasky" / "hooks"
    manifest = json.loads((hooks_dir / "hook.json").read_text(encoding="utf-8"))
    assert any(entry["event"] == "task.pre_add" for entry in manifest["hooks"])
    assert (hooks_dir / "sample_pre_add.py").exists()
    assert (hooks_dir / "sample_post_add.py").exists()


def test_project_hooks_scaffold_requires_force(tmp_path: Path, monkeypatch) -> None:
    _init_project(tmp_path, monkeypatch)

    first = runner.invoke(cli_app, ["project", "hooks", "scaffold"])
    assert first.exit_code == 0

    second = runner.invoke(cli_app, ["project", "hooks", "scaffold"])
    assert second.exit_code == 1
    assert "Hook files already exist" in second.stdout

    forced = runner.invoke(cli_app, ["project", "hooks", "scaffold", "--force"])
    assert forced.exit_code == 0


def test_project_hooks_scaffold_minimal(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)

    result = runner.invoke(cli_app, ["project", "hooks", "scaffold", "--minimal"])
    assert result.exit_code == 0

    hooks_dir = project_dir / ".tasky" / "hooks"
    manifest = json.loads((hooks_dir / "hook.json").read_text(encoding="utf-8"))
    assert manifest["hooks"] == []


def test_task_update_requires_fields(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)
    tasks_file = project_dir / ".tasky" / "tasks.json"

    add = runner.invoke(
        cli_app,
        [
            "task",
            "add",
            "--name",
            "Sample",
            "--details",
            "Details",
        ],
    )
    assert add.exit_code == 0
    task_id = json.loads(tasks_file.read_text(encoding="utf-8"))["tasks"][0]["task_id"]

    result = runner.invoke(cli_app, ["task", "update", task_id])
    assert result.exit_code == 2


def test_task_export_uses_filters_and_files(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)

    add_one = runner.invoke(
        cli_app,
        [
            "task",
            "add",
            "--name",
            "Alpha",
            "--details",
            "Details",
        ],
    )
    assert add_one.exit_code == 0
    add_two = runner.invoke(
        cli_app,
        [
            "task",
            "add",
            "--name",
            "Beta",
            "--details",
            "More",
        ],
    )
    assert add_two.exit_code == 0

    tasks_path = project_dir / ".tasky" / "tasks.json"
    task_entries = json.loads(tasks_path.read_text(encoding="utf-8"))
    second_id = task_entries["tasks"][1]["task_id"]
    runner.invoke(cli_app, ["task", "complete", second_id])

    stdout_export = runner.invoke(cli_app, ["task", "export"])
    assert stdout_export.exit_code == 0
    payload = json.loads(stdout_export.stdout.strip())
    assert len(payload) == 2

    completed_export = runner.invoke(cli_app, ["task", "export", "--completed"])
    assert completed_export.exit_code == 0
    completed_payload = json.loads(completed_export.stdout.strip())
    assert len(completed_payload) == 1
    assert completed_payload[0]["name"] == "Beta"

    pending_export = runner.invoke(cli_app, ["task", "export", "--pending"])
    assert pending_export.exit_code == 0
    pending_payload = json.loads(pending_export.stdout.strip())
    assert len(pending_payload) == 1
    assert pending_payload[0]["name"] == "Alpha"

    export_path = project_dir / "tasks-export.json"
    to_file = runner.invoke(
        cli_app,
        ["task", "export", "--file", str(export_path)],
    )
    assert to_file.exit_code == 0
    on_disk = json.loads(export_path.read_text(encoding="utf-8"))
    assert len(on_disk) == 2

    collision = runner.invoke(
        cli_app,
        ["task", "export", "--file", str(export_path)],
    )
    assert collision.exit_code != 0
    forced = runner.invoke(
        cli_app,
        ["task", "export", "--file", str(export_path), "--force"],
    )
    assert forced.exit_code == 0
def test_project_config_command_prints_and_updates(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)
    config_path = project_dir / ".tasky" / "config.json"

    view = runner.invoke(cli_app, ["project", "config"])
    assert view.exit_code == 0
    assert '"tasks_file": "tasks.json"' in view.stdout

    update = runner.invoke(
        cli_app,
        [
            "project",
            "config",
            "--set",
            "tasks_file=tasks.sqlite",
            "--force",
        ],
    )
    assert update.exit_code == 0
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["tasks_file"] == "tasks.sqlite"
    sqlite_path = project_dir / ".tasky" / "tasks.sqlite"
    assert sqlite_path.exists()


def test_project_config_requires_confirmation_without_force(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)
    config_path = project_dir / ".tasky" / "config.json"

    result = runner.invoke(
        cli_app,
        ["project", "config", "--set", "tasks_file=tasks.sqlite"],
        input="y\n",
    )
    assert result.exit_code == 0
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["tasks_file"] == "tasks.sqlite"


def test_project_config_rejects_invalid_set_syntax(tmp_path: Path, monkeypatch) -> None:
    _init_project(tmp_path, monkeypatch)
    result = runner.invoke(cli_app, ["project", "config", "--set", "invalid"])
    assert result.exit_code != 0


def test_project_post_init_hook_runs(tmp_path: Path, monkeypatch) -> None:
    project_dir = tmp_path / "workspace"
    hooks_dir = project_dir / ".tasky" / "hooks"
    hooks_dir.mkdir(parents=True)
    script = hooks_dir / "post_init.py"
    script.write_text(
        """
import json, sys, os
from pathlib import Path
payload = json.load(sys.stdin)
log_path = Path(payload["project_path"]) / ".tasky" / "post_init.log"
log_path.write_text(json.dumps(payload), encoding="utf-8")
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    manifest = {
        "version": 1,
        "hooks": [
            {
                "id": "post-init",
                "event": "project.post_init",
                "command": [sys.executable, "post_init.py"],
            }
        ],
    }
    (hooks_dir / "hook.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.chdir(project_dir)

    result = runner.invoke(cli_app, ["project", "init"])

    assert result.exit_code == 0
    log_path = project_dir / ".tasky" / "post_init.log"
    assert log_path.exists()


def test_project_post_forget_hook_runs(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)
    hooks_dir = project_dir / ".tasky" / "hooks"
    hooks_dir.mkdir(parents=True)
    script = hooks_dir / "post_forget.py"
    script.write_text(
        """
import json, sys, os
from pathlib import Path
payload = json.load(sys.stdin)
log_path = Path(os.environ["TASKY_HOOKS_DIR"]) / "post_forget.log"
log_path.write_text(json.dumps(payload), encoding="utf-8")
""",
        encoding="utf-8",
    )
    script.chmod(0o755)
    manifest = {
        "version": 1,
        "hooks": [
            {
                "id": "post-forget",
                "event": "project.post_forget",
                "command": [sys.executable, "post_forget.py"],
            }
        ],
    }
    (hooks_dir / "hook.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = runner.invoke(cli_app, ["project", "unregister", "--force"])

    assert result.exit_code == 0
    log_path = hooks_dir / "post_forget.log"
    assert log_path.exists()


def _write_hook_scripts(hooks_dir: Path, scripts: dict[str, str]) -> None:
    for name, content in scripts.items():
        script_path = hooks_dir / name
        script_path.write_text(content.lstrip(), encoding="utf-8")
        script_path.chmod(0o755)


def _init_project(tmp_path: Path, monkeypatch) -> Path:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)
    result = runner.invoke(cli_app, ["project", "init"])
    assert result.exit_code == 0
    return project_dir


def test_project_register_restores_forgotten_entry(tmp_path: Path, monkeypatch) -> None:
    project_dir = _init_project(tmp_path, monkeypatch)

    forget = runner.invoke(cli_app, ["project", "unregister", "--force"])
    assert forget.exit_code == 0
    assert (project_dir / ".tasky").exists()

    register = runner.invoke(cli_app, ["project", "register"])
    assert register.exit_code == 0
    assert "Registered project" in register.stdout
