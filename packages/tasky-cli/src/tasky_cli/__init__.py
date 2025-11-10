from __future__ import annotations

import typer

from .commands import project_app, task_app

app = typer.Typer(no_args_is_help=True, add_completion=False)

app.add_typer(project_app, name="project")
app.add_typer(task_app, name="task")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
