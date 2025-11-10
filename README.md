# tasky
Task manager with LLMs in mind.

## Architecture Overview
- `packages/tasky-tasks` hosts the task domain: immutable `TaskModel` definitions, validation rules, and orchestration services such as `TaskService`. It also publishes repository protocols (`tasky_tasks.ports`) that describe how persistence layers must behave.
- `packages/tasky-projects` coordinates workspace-level concepts like registries and project metadata. It composes multiple task services while remaining free of infrastructure concerns.
- `packages/tasky-storage` implements the repository protocols using concrete backends (JSON files today, additional adapters later). Each backend is responsible for translating between domain models and its storage representation.
- `packages/tasky-hooks` defines lifecycle events and default dispatchers so hosts can react to changes (task created, project pruned, etc.) without coupling directly to domain internals.
- `packages/tasky-settings` acts as the composition root. It reads configuration, selects the desired storage backend, wires the domain services, and exposes ready-to-use bundles for hosts.
- `packages/tasky-cli` provides the Typer-based command line interface. Commands accept the services assembled by `tasky-settings`, marshal user input, and render results.
- `src/tasky` is a thin entry point that forwards to `tasky-cli`, making it easy to ship additional front-ends without duplicating bootstrap code.

## Developer Workflow
- Install dependencies with `uv sync`, lint via `uv run ruff check`, and run the full suite with `uv run pytest`.
- When writing new features, inject domain services or repositories instead of instantiating them inline so logic stays testable.
- Add tests next to the code they exercise (`packages/<pkg>/tests/`) and use storage fakes or hooks test doubles to isolate scenarios.
- `tasky task import` supports multiple strategies (`append`, `replace`, `merge`); extend the storage adapters or domain services to introduce new behaviors.
- Task maintenance commands (`tasky task complete`, `tasky task reopen`, `tasky task update`) delegate to `TaskService` so invariants stay centralized and hooks fire consistently.
- Project configuration flows through `tasky project config`; settings choose the proper repository implementation, migrate data when necessary, and keep CLI users insulated from infrastructure details.
