from __future__ import annotations

import typer

from .commands import common as common_commands
from .commands import project_app, task_app
from .context import ensure_cli_context

app = typer.Typer(no_args_is_help=True, add_completion=False)

app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")

common_commands.register_command_middleware(common_commands.structured_logging_middleware)


@app.callback(invoke_without_command=True)
def app_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Print structured command logs.",
    ),
) -> None:
    ensure_cli_context(ctx, verbose=verbose)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
