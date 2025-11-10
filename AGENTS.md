# Repository Guidelines

## Project Structure & Module Organization
The CLI entry lives in `src/tasky`, while reusable modules live under `packages/` (`tasky-core`, `tasky-models`, `tasky-storage`, `tasky-cli`, `tasky-settings`). Each package keeps implementation code in `src/` and exports type hints via `py.typed`. Add use-case orchestration to `tasky-core`, immutable schemas to `tasky-models`, storage or external adapters to `tasky-storage`, and presentation logic to `tasky-cli`. Place tests beside the code they exercise (e.g., `packages/tasky-core/tests/`) or under a shared `tests/` directory for cross-package scenarios.

## Build, Test, and Development Commands
- `uv sync` installs the workspace dependencies declared in `pyproject.toml`.
- `uv run tasky` executes the CLI entry point for smoke checks.
- `uv run pytest` (optionally `-k <pattern>`) runs the project test suite.
- Always execute ad-hoc Python via `uv run python …` (e.g., `uv run python -m <module>`), and run tools like Ruff through `uv run ruff …` so everything stays inside the managed environment.
- End every coding session by running `uv run pytest` followed by `uv run ruff check --fix` to keep tests and linting green before handing off.

## Coding Style & Naming Conventions
Target Python ≥3.13, 4-space indentation, and full type hints. Order imports as standard library, third-party, local. Name Pydantic classes with clear suffixes (`TaskModel`, `WorkspaceConfig`) and protocols in `tasky-core` with `Port` or `Protocol` (`TaskRepositoryPort`). Keep orchestration pure inside the core and isolate side effects within adapters. Run your preferred formatter/linter (e.g., `ruff format`, `ruff check`) before submitting changes.

- We do **not** keep deprecated or legacy code around. When refactoring a feature, remove the old implementation entirely rather than keeping transitional layers or toggles. The repo should reflect the current architecture at all times.

## Testing Guidelines
Adopt `pytest` for unit and integration coverage. Name files `test_<subject>.py` and choose descriptive test functions (`test_create_task_sets_default_priority`). Use the protocol seams to swap real adapters for fakes when exercising the core. Add integration tests for each storage backend using temp directories or ephemeral databases, and prioritise flows central to the task lifecycle (create → schedule → complete) before layering LLM automation.

## Commit & Pull Request Guidelines
Current history is minimal (`Initial commit`), so set the bar with imperative, 72-character subject lines (`Add sqlite task repository`). Reference issue numbers when available and include concise body context. Pull requests should describe the change, list tests executed (`uv run pytest`), and attach screenshots or CLI transcripts for user-facing updates. Keep PRs focused on a single feature or fix to streamline review.

## Architecture Notes
Maintain the clean-layer design: domain types in `tasky-models`, orchestration in `tasky-core`, swappable adapters in `tasky-storage`, and configuration wiring in `tasky-settings`. When expanding behaviour, extend or decorate protocols instead of coupling services to concrete adapters. This discipline keeps upcoming MCP/LLM integrations drop-in while preserving a predictable task workflow.
