# Repository Guidelines

## Module Focus
`tasky-cli` delivers the Typer-powered command-line interface. Commands should translate user input into calls to `tasky-core` services without embedding business logic. Keep command handlers skinny, delegating validation and orchestration to the core.

### Input & Help Behaviour
- Every command (root or subcommand) must show its help output when invoked without the required arguments/options—use Typer’s `no_args_is_help=True` to enforce this consistently.
- Project lifecycle commands live under the `project` sub-app (`tasky project init/list/forget/prune`); task operations live under the `task` sub-app (`tasky task list/add/remove`). Keep new commands aligned with these groups.
- Add new CLI functionality by extending the modules in `tasky_cli.commands`. Each module exposes a `register(app)` function so the root CLI stays lean.
- Provide explicit registry maintenance commands (`tasky project prune`) instead of implicit cleanup so users can preview actions (`--dry-run`) before deletion.
- Bulk task creation goes through `tasky task import`, which accepts nested JSON via `--file` or STDIN and uses `--strategy append|replace|merge` to control persistence. Keep future automation-friendly commands similarly structured (file/STDIN input, clear validation errors).

## Project Layout
Implementation lives in `src/tasky_cli/`. Organise commands under `commands/` (e.g., `commands/tasks.py`) and keep CLI bootstrapping in `__main__.py` or `app.py`. Shared presentation utilities (formatters, table printers) belong in `ui/`. Re-export the assembled Typer `app` from `src/tasky_cli/__init__.py` for reuse by other entry points.

## Development Commands
- `uv sync` prepares the environment with Typer and the declared dependencies.
- `uv run python -m tasky_cli` executes the Typer app for manual testing.
- `uv run python -m tasky_cli --help` is a quick check that command registration remains healthy.

## Coding Style & Conventions
Use Typer’s callback signatures with explicit type hints for options and arguments. Prefer command functions named with verbs (`create_task`, `list_tasks`) and group them with Typer sub-apps for logical domains. Keep output consistent—use helper functions for colors or formatting rather than inline ANSI codes. Refrain from performing I/O beyond stdout/stderr; offload data access to injected services.

## Testing Guidance
Leverage `pytest` with Typer’s `CliRunner` to simulate command invocations. Store CLI tests in `tests/commands/test_<command>.py` and assert on exit codes, stdout, and side effects triggered via mocked services. Cover error cases (invalid options, missing configuration) to ensure helpful messaging.

## Commit & Review Expectations
Craft imperative, ≤72-character subjects (`Add task list command`). Pull requests should describe new commands, flag any user-facing output changes, and attach example sessions when appropriate. Verification steps must include CLI runs (`uv run python -m tasky_cli`) and targeted tests (`uv run pytest`).

## Architectural Notes
Respect the dependency direction: CLI imports `tasky-core` and configuration builders but never storage adapters directly. Any new command requiring extra behaviour should request it through the composition root so the implementation remains swappable, and document the wiring in the entry-point (`__main__.py`/`app.py`) for clarity. Keep startup logic idempotent to support embedding the CLI in other hosts (e.g., MCP servers).
