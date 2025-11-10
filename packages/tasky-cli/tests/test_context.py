from __future__ import annotations

import click
from typer import Context

from tasky_cli.context import CLIContext, ensure_cli_context


def test_ensure_cli_context_creates_and_reuses_instance() -> None:
    ctx = Context(click.Command("dummy"))

    context = ensure_cli_context(ctx, verbose=True)

    assert isinstance(context, CLIContext)
    assert context.verbose is True
    assert ctx.obj is context
    reused = ensure_cli_context(ctx)
    assert reused is context
    assert reused.verbose is True
