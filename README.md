# tasky
Task manager with LLMs in mind.

## Architecture Overview
- **Domain core** lives in `tasky-core` where `TaskUseCases`, `TaskFactory`, and `TaskTree` orchestrate validation, traversal, and repository interactions. `TaskService` simply wires these policies together so adapters can swap implementations without changing callers (see `docs/core-architecture.md`).
- **Settings & registry** concerns live in `tasky-settings`, which now exposes a `ProjectSettingsService`, `TaskRepositoryFactory`, and `ConfigRepository` helper. They encapsulate filesystem layout, repository wiring, and registry updates while keeping side effects behind testable seams (details in `docs/settings-architecture.md`).
- `TaskySettings` configures the global registry backend (`registry_backend=json|sqlite`); when SQLite is selected, the service migrates the legacy JSON registry into `projects.db` automatically and keeps subsequent CLI commands concurrent-safe.
- **CLI composition** is handled by Typer sub-apps plus a tiny dependency container (`tasky_cli.deps`). Commands receive a ready-made `CLIContext` via the `command_action` decorator (no need to poke `typer.Context.obj`) and delegate rendering to `tasky_cli.ui.*` (documented in `docs/cli-structure.md`).

## Developer Workflow
- Install dependencies with `uv sync`, lint via `uv run ruff check`, and run the full suite with `uv run pytest`.
- When writing new features, prefer injecting dependencies (e.g., `TaskUseCases`, `ProjectSettingsService`) so logic stays testable. For reference implementations across packages, review `docs/project-structure.md` and `docs/settings-architecture.md`.
- Add tests next to the code they exercise (package-level `tests/` folders) and use the dependency container overrides (`tasky_cli.deps.configure_dependencies/reset_dependencies`) for CLI-focused tests.
- Task imports support strategies via `tasky task import --strategy append|replace|merge`; extend `tasky_core.importers` to add more behaviors.
- Task maintenance commands (`tasky task complete`, `tasky task reopen`, `tasky task update --name/--details`) toggle completion state or edit content in place, firing the corresponding hook events so automations stay informed.
- `tasky task export [--file path] [--completed|--pending]` snapshots tasks using the same JSON schema consumed by `tasky task import`, making round-trips straightforward. Use `--force` to overwrite an existing export file.
- Project metadata stays declarative: run `tasky project config` to review or set `.tasky/config.json` fields (e.g., switch `tasks_file` to SQLite). The service migrates tasks automatically and guards against destructive changes unless `--force` is supplied.
- Project progress is cached in the registry so `tasky project list` stays fast; pass `--refresh-progress` when you need to recompute counts after out-of-band edits.
- CLI commands receive a shared `CLIContext` via `typer.Context.obj`, giving access to the Rich console plus Task/Project services; prefer `get_cli_context(ctx)` over importing factories directly.
- Storage adapters: `JsonDocumentStore` powers the file-based workflow, while the new `SQLiteTaskRepository` gives larger workspaces a normalized relational backend (no more JSON blobs inside SQLite).
- Domain models expose behavior: `Task` aggregates include helper methods (`add_subtask`, `remove_subtask`, `mark_complete`, etc.) so invariants (timestamps, completion state) stay near the data and tests can exercise them directly.
