"""Tasky CLI package entry point."""

from __future__ import annotations

import typer
from tasky_logging import configure_logging
from tasky_settings import get_settings

from .commands import project_app, task_app

app = typer.Typer(no_args_is_help=True, add_completion=False)

app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity level. Use -v for INFO, -vv for DEBUG.",
    ),
) -> None:
    """Configure global settings for Tasky CLI.

    Settings are loaded from multiple sources in order of precedence:
    1. Model defaults (lowest)
    2. Global config (~/.tasky/config.toml)
    3. Project config (.tasky/config.toml)
    4. Environment variables (TASKY_*)
    5. CLI flags (highest)

    The verbose flag (-v, -vv) overrides logging verbosity from config files.
    """
    # Build CLI overrides from verbose flag
    # Cap verbosity at 2 (DEBUG level is the maximum)
    cli_overrides = {}
    if verbose > 0:
        cli_overrides = {"logging": {"verbosity": min(verbose, 2)}}

    # Load settings from hierarchical sources
    settings = get_settings(cli_overrides=cli_overrides)

    # Configure logging from settings
    configure_logging(settings.logging)

    # Store settings in context for commands to use
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


def main() -> None:
    """Run the Tasky CLI application."""
    app()


if __name__ == "__main__":
    main()
