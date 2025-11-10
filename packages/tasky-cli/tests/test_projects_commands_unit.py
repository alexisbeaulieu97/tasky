from __future__ import annotations

from io import StringIO
from pathlib import Path
from rich.console import Console

import click

from tasky_cli.commands import projects as project_commands
from tasky_cli.context import CLIContext
from tasky_core.projects.context import get_project_context, ProjectContext
from tasky_core.projects.registry import ProjectRegistryEntry


def _dummy_task_service(_: Path | None = None) -> None:
    raise AssertionError("Task service should not be requested in project command unit tests.")


def _dummy_project_query_service():
    class _Query:
        def list_overviews(self, *, include_missing: bool = False, refresh_cache: bool = False):
            return []

    return _Query()


class StubProjectSettings:
    def __init__(self, context: ProjectContext) -> None:
        self._context = context
        self.initialised = False
        self.is_project_initialised_calls: list[Path] = []
        self.initialise_calls: list[tuple[Path, bool]] = []
        self.prune_called = False
        self.unregister_calls: list[tuple[Path, bool]] = []

    # Methods exercised by commands
    def is_project_initialised(self, project_path: Path | None = None) -> bool:
        assert project_path is not None
        self.is_project_initialised_calls.append(project_path)
        return self.initialised

    def initialise_project(self, project_path: Path | None = None, *, force: bool = False):
        assert project_path is not None
        self.initialise_calls.append((project_path, force))
        return self._context

    def get_project_context(self, project_path: Path | None = None) -> ProjectContext:
        assert project_path is not None
        return self._context

    def register_project(self, project_path: Path) -> ProjectRegistryEntry:
        return ProjectRegistryEntry(path=project_path)

    def prune_missing_projects(self) -> list[ProjectRegistryEntry]:
        self.prune_called = True
        return [
            ProjectRegistryEntry(path=self._context.project_path),
        ]

    def unregister_project(self, project_path: Path, *, purge: bool = False) -> None:
        self.unregister_calls.append((project_path, purge))


def _make_context(settings: StubProjectSettings) -> CLIContext:
    console = Console(file=StringIO(), force_terminal=False, color_system=None)
    return CLIContext(
        console=console,
        settings_service=settings,  # type: ignore[arg-type]
        task_service_factory=_dummy_task_service,
        project_query_factory=_dummy_project_query_service,
    )


def _invoke(command, cli_context, *args, **kwargs):
    ctx = click.Context(click.Command(command.__name__), obj=cli_context)
    with ctx.scope():
        return command(cli_context, *args, **kwargs)


def test_project_init_uses_context_settings(tmp_path: Path) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    context = get_project_context(project_dir)
    settings = StubProjectSettings(context)
    cli_context = _make_context(settings)

    _invoke(project_commands.init_command, cli_context, path=project_dir)

    assert settings.is_project_initialised_calls == [project_dir.resolve()]
    assert settings.initialise_calls == [(project_dir.resolve(), False)]


def test_project_prune_invokes_settings_service_when_not_dry_run(tmp_path: Path) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    settings = StubProjectSettings(get_project_context(project_dir))
    cli_context = _make_context(settings)

    _invoke(project_commands.project_prune_command, cli_context, dry_run=False)

    assert settings.prune_called is True


def test_project_unregister_uses_settings_service(tmp_path: Path) -> None:
    project_dir = tmp_path / "workspace"
    project_dir.mkdir()
    metadata_dir = project_dir / ".tasky"
    metadata_dir.mkdir(parents=True)
    settings = StubProjectSettings(get_project_context(project_dir))
    cli_context = _make_context(settings)

    _invoke(
        project_commands.project_unregister_command,
        cli_context,
        path=project_dir,
        force=True,
    )

    assert settings.unregister_calls == [(project_dir.resolve(), False)]
