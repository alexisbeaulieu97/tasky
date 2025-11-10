# Repository Guidelines

## Module Focus
`tasky-core` hosts application services and domain orchestration. Keep business logic here by defining services (`TaskService`, `SchedulingService`) and narrow protocols (`TaskRepositoryPort`, `TaskSchedulerPort`). Avoid direct infrastructure calls—inject them through constructor arguments so behaviour stays swappable.

## Project Layout
Source lives in `src/tasky_core/`. Place new services under `services/`, protocol definitions in `ports/`, and shared utilities in `utils/`. Export the public surface in `src/tasky_core/__init__.py`. If a change introduces cross-cutting helpers, consider a `middleware/` submodule to keep services lean. Put tests in `tests/` mirroring the module tree (`tests/services/test_task_service.py`).

## Development Commands
- `uv sync` installs or updates the package dependencies defined in this project.
- `uv run pytest` (optionally `tests/services -k <pattern>`) runs the core test suite.
- `uv run python -m tasky_core.demo` is suitable for temporary smoke scripts; delete the module once the experiment is complete.

## Coding Style & Conventions
Target Python ≥3.13 with 4-space indentation and complete type hints. Protocols end in `Port` or `Protocol`. Service classes use imperative verbs (`assign`, `schedule`) and expose small method surfaces. Keep orchestration free of side effects; delegate persistence, notifications, or LLM calls to injected ports. Document tricky flows with short docstrings rather than inline comments.

## Testing Guidance
Use `pytest` with descriptive names (`test_schedule_task_sets_due_date`). Mock ports via simple dataclasses or `unittest.mock` to keep tests deterministic. When behaviour depends on time or UUIDs, inject test doubles via protocols (`ClockPort`, `IdGeneratorPort`). Add integration-style tests only when coordinating multiple services; otherwise isolate unit tests to a single service.

## Commit & Review Expectations
Write imperative subject lines limited to 72 characters (`Refine recurring task scheduling`). Include a short body describing behavioural impact and list executed tests (`uv run pytest`). Pull requests should link relevant issues and call out protocol updates so integrators can react. Keep diffs focused on a single concern to ease review.

## Architectural Notes
Respect the clean-layer contract: the core owns orchestration, never concrete adapters. When you need new behaviour, add or extend a protocol and let callers supply the implementation via `tasky-storage` or other infrastructure packages. Keep this package importable without side effects so the CLI, tests, or future MCP integrations can compose it predictably.
