from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import typer
from rich.console import Console

from tasky_core import TaskService
from tasky_settings import ProjectQueryService, ProjectSettingsService

from . import deps

TaskServiceFactory = Callable[[Path | None], TaskService]
ProjectQueryFactory = Callable[[], ProjectQueryService]


@dataclass
class CLIContext:
    console: Console
    settings_service: ProjectSettingsService
    task_service_factory: TaskServiceFactory
    project_query_factory: ProjectQueryFactory
    verbose: bool = False

    def task_service(self, project_path: Path | None = None) -> TaskService:
        return self.task_service_factory(project_path)

    def project_query_service(self) -> ProjectQueryService:
        return self.project_query_factory()

    def settings(self) -> ProjectSettingsService:
        return self.settings_service


def build_cli_context(
    console: Console | None = None,
    *,
    verbose: bool = False,
) -> CLIContext:
    return CLIContext(
        console=console or Console(),
        settings_service=deps.get_settings_service(),
        task_service_factory=deps.get_task_service,
        project_query_factory=deps.get_project_query_service,
        verbose=verbose,
    )


def ensure_cli_context(
    ctx: typer.Context,
    *,
    verbose: bool | None = None,
) -> CLIContext:
    context = ctx.obj
    if isinstance(context, CLIContext):
        if verbose is not None:
            context.verbose = verbose
        return context
    context = build_cli_context(verbose=verbose or False)
    ctx.obj = context
    return context


def get_cli_context(ctx: typer.Context) -> CLIContext:
    context = ctx.obj
    if isinstance(context, CLIContext):
        return context
    return ensure_cli_context(ctx)
