<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Guidelines

## Project Structure & Module Organization
- This workspace follows Domain-Driven Design / Clean Architecture: domains publish their models and ports, infrastructure implements those ports, settings compose the graph, and presentation layers consume the composed services.
- `src/tasky`: CLI entry point and minimal glue for user interactions. It simply forwards to `tasky-cli` so the workspace can install multiple front-ends without duplicating boot code.
- `packages/tasky-cli`: presentation layer built on Typer. Commands marshal user intent, call into the task/project services exported by the feature packages, and format results. No persistence or configuration logic belongs here.
- `packages/tasky-tasks`: task domain models plus orchestration services (`TaskModel`, `TaskService`, validators). It owns task-centric business rules and publishes the repository protocols that storage adapters implement.
- `packages/tasky-projects`: project/workspace domain concerns (registries, metadata, task collections). It coordinates multiple task services when needed but still stays pure—no filesystem or CLI code.
- `packages/tasky-hooks`: automation surface for emitting and handling lifecycle events (task created, project pruned, etc.). Define hook contracts, default dispatchers, and test doubles here so storage/CLI layers can subscribe without tight coupling.
- `packages/tasky-storage`: infrastructure adapters that implement the repository protocols published by the feature packages (e.g., `TaskRepository` from `tasky-tasks`). Keep backend-specific helpers (migrations, serializers) close to their adapter modules so swapping persistence stays a configuration change.
- `packages/tasky-settings`: configuration and wiring. Use `pydantic-settings` to read env vars or config files, choose the proper storage adapters, and assemble ready-to-use service bundles for hosts (CLI, MCP servers, tests).
- Tests sit beside the code they cover (`packages/<pkg>/tests/`), with optional cross-package scenarios under `tests/` for full CLI flows or multi-backend integration cases.

## Build, Test, and Development Commands
- `uv sync` installs the workspace dependencies declared in `pyproject.toml`.
- `uv run tasky` executes the CLI entry point for smoke checks.
- `uv run pytest` (optionally `-k <pattern>`) runs the project test suite.
- `uv run pytest --cov=packages --cov-report=html` runs tests with coverage measurement and generates an HTML report in `htmlcov/`.
- `uv run pytest --cov=packages --cov-fail-under=80` enforces the 80% coverage threshold and fails if not met.
- Always execute ad-hoc Python via `uv run python …` (e.g., `uv run python -m <module>`), and run tools like Ruff through `uv run ruff …` so everything stays inside the managed environment.
- End every coding session by running `uv run pytest`, `uv run ruff check --fix`, **and** `uv run pyright` so tests, lint, and static typing stay green before handing off.

## Test Coverage
The project enforces a minimum of 80% test coverage across all packages. Coverage is measured using `pytest-cov` and configured in `pyproject.toml`.

**Running coverage reports:**
```bash
# Run tests with terminal coverage report
uv run pytest --cov=packages --cov-report=term-missing

# Generate HTML coverage report (opens in browser)
uv run pytest --cov=packages --cov-report=html

# Enforce 80% threshold (fails if below)
uv run pytest --cov=packages --cov-fail-under=80
```

**Coverage Configuration:**
- Branch coverage is enabled to ensure all conditional paths are tested
- Test files, `__init__.py`, and `conftest.py` are excluded from coverage measurement
- Non-testable patterns (e.g., `if __name__ == "__main__"`, `TYPE_CHECKING` blocks) are excluded
- HTML reports are generated to `htmlcov/` directory (git-ignored)

**Adding coverage exceptions:**
Use `# pragma: no cover` for legitimate exclusions (e.g., defensive error handlers that are difficult to trigger in tests).

## Coding Style & Naming Conventions
Target Python ≥3.13, 4-space indentation, and full type hints. Order imports as standard library, third-party, local. Name Pydantic classes with descriptive suffixes (`TaskModel`, `ProjectMetadata`) and keep services/action classes verb-based (`TaskService`, `ProjectRegistry`). Repository interfaces live with their feature package (e.g., `tasky_tasks.ports.TaskRepository`) while hook contracts in `tasky-hooks` end with `Event` or `Handler`. Keep orchestration helpers pure inside the feature packages and isolate side effects within adapters. Run your preferred formatter/linter (e.g., `ruff format`, `ruff check`) before submitting changes.

- We do **not** keep deprecated or legacy code around. When refactoring a feature, remove the old implementation entirely rather than keeping transitional layers or toggles. The repo should reflect the current architecture at all times.

## Testing Guidelines
Adopt `pytest` for unit and integration coverage. Name files `test_<subject>.py` and choose descriptive test functions (`test_create_task_sets_default_priority`). Lean on repository protocols to swap real adapters for fakes when exercising `tasky-tasks` or `tasky-projects`. Add backend-specific integration suites under `tasky-storage/tests/` that hit real JSON/SQLite files, and wire full-stack tests (settings → CLI) when validating new configuration or hook flows. Prioritise the central lifecycle (create → schedule → complete) before layering LLM automation.

**Coverage requirements:** All new code must maintain ≥80% test coverage. Check coverage locally before submitting changes using `uv run pytest --cov=packages --cov-fail-under=80`.

## Commit & Pull Request Guidelines
Current history is minimal (`Initial commit`), so set the bar with imperative, 72-character subject lines (`Add sqlite task repository`). Reference issue numbers when available and include concise body context. Pull requests should describe the change, list tests executed (`uv run pytest`), and attach screenshots or CLI transcripts for user-facing updates. Keep PRs focused on a single feature or fix to streamline review.

## Architecture Notes
Maintain the clean-layer design: feature domains (`tasky-tasks`, `tasky-projects`) expose pure models/services plus their repository interfaces, storage implements those interfaces, hooks broadcast lifecycle signals, settings wires everything, and the CLI (or any host) consumes the assembled services. Each new capability follows the same flow—define the schema, rules, and ports inside the relevant feature package, implement the ports inside `tasky-storage`, register hook events in `tasky-hooks`, and let `tasky-settings` expose a ready-made bundle to `tasky-cli`. Keep adapters swappable by depending only on the published protocols, and remove legacy code instead of keeping transitional toggles so the repo always reflects the active architecture.

**Architecture Decision Records (ADRs)**: Key architectural decisions are documented in `docs/architecture/adr/`. Read these to understand why the system is structured the way it is:
- [ADR-001: Backend Registry Pattern](docs/architecture/adr/0001-backend-registry-pattern.md) - How backends self-register without coupling
- [ADR-002: Error Handling Strategy](docs/architecture/adr/0002-error-handling-strategy.md) - Protocol-based error decoupling
- [ADR-003: Configuration Hierarchy](docs/architecture/adr/0003-configuration-hierarchy.md) - Settings precedence order
- [ADR-004: Project Registry Storage](docs/architecture/adr/0004-project-registry-storage.md) - Why JSON instead of SQLite

See [docs/architecture/adr/README.md](docs/architecture/adr/README.md) for the full ADR index and how to create new ADRs.
