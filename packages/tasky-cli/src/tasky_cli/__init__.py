"""Tasky CLI package entry point."""

from __future__ import annotations

import typer
from tasky_logging import configure_logging

from .commands import project_app, task_app

app = typer.Typer(no_args_is_help=True, add_completion=False)

app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")


@app.callback()
def main_callback(
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity level. Use -v for INFO, -vv for DEBUG.",
    ),
) -> None:
    """Configure global settings for Tasky CLI."""
    configure_logging(verbosity=verbose)


def main() -> None:
    """Run the Tasky CLI application."""
    app()


if __name__ == "__main__":
    main()
