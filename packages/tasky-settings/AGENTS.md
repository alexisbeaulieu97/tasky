# Repository Guidelines

## Module Focus
`tasky-settings` centralises configuration using `pydantic-settings`. It should expose typed configuration objects (`TaskyConfig`, `StorageConfig`) and helper factories that assemble adapters or service dependencies. Avoid embedding business rules; instead translate environment variables, files, or CLI flags into structured settings consumed by the application layer.

### Layering
- Delegate domain logic (project registry, task traversal, etc.) to `tasky-core`. Settings should focus on resolving paths/env vars and calling core helpers.
- Keep adapter wiring (e.g., building `JsonDocumentStore` instances from the configured paths) in thin helper functions so other hosts can reuse them.

## Project Layout
Source code resides in `src/tasky_settings/`. Group settings by concern (`storage.py`, `llm.py`, `cli.py`) and re-export curated classes/functions through `src/tasky_settings/__init__.py`. Keep defaults and environment variable prefixes close to their definitions. If you add configuration loaders, place them in `loaders/` to separate I/O from schema declarations.

## Development Commands
- `uv sync` keeps Pydantic Settings and declared dependencies aligned.
- `uv run python -m tasky_settings.check` can host quick validation scripts for new configuration schemas; remove temporary modules after review.
- `uv run pytest` runs schema and loader tests.

## Coding Style & Conventions
Use `BaseSettings` subclasses with explicit field descriptions, env aliases, and sensible defaults. Name classes with the suffix `Config` (`StorageBackendConfig`). Keep configuration pure—no API calls or file reads inside property setters. Provide helper functions (`build_task_repository(config: StorageConfig)`) that translate configuration into concrete objects while remaining side-effect free unless explicitly documented.

## Testing Guidance
Write `pytest` cases that exercise field validation, default resolution, and environment override precedence. Use `monkeypatch` to simulate env vars. Snapshot configurations (`assert config.model_dump() == {...}`) to prevent accidental schema drift. When factories instantiate adapters, mock the external constructors to keep tests fast and deterministic.

## Commit & Review Expectations
Subjects stay imperative and concise (`Add llm provider settings`). Pull requests must detail new environment variables, defaults, and migration expectations. Include verification notes such as `uv run pytest` and document any manual checks (`TASKY_STORAGE_BACKEND=file uv run python -m your_host_app`) when behaviour changes.

## Architectural Notes
Ensure configuration objects remain decoupled from specific adapters so swapping implementations only requires adjusting settings. Any new external dependency should surface through clearly named configuration fields and factories, and document how composition roots consume them so downstream hosts can wire dependencies consistently. This keeps the clean-layer composition strategy intact across the workspace.
