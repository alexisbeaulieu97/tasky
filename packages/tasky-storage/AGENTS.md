# Repository Guidelines

## Module Focus
`tasky-storage` provides infrastructure adapters for persistence and related I/O. Each backend (SQLite, Postgres, file-based) should implement the repository or document-store protocols defined by the application layer. Keep adapters thin: transform domain models to storage DTOs, invoke the backend, and convert results back to domain objects.

## Project Layout
Source files live in `src/tasky_storage/`. Create a subpackage per backend (`sqlite/`, `memory/`) with a public factory (`build_store(config: StorageConfig)`). Shared DTOs and mapping helpers belong in `mappers.py` or `schemas.py`. Export supported factories through `src/tasky_storage/__init__.py` so composition roots can import them without touching internals.

## Development Commands
- `uv sync` installs backend drivers declared in the package dependencies.
- `uv run pytest` executes adapter-specific tests (use `tests/sqlite -k <pattern>` to focus).
- `uv run python -m tasky_storage.sqlite.migrate` can host migration utilities; keep them idempotent and documented.

## Coding Style & Conventions
Adapters should be class-based when maintaining stateful connections or module-level functions when stateless. Name classes with the backend first (`SqliteDocumentStore`). Use context managers for connections and commit explicitly on write operations. Validate configuration upfront, raising `StorageConfigurationError` (define locally) when inputs are invalid. Avoid leaking backend exceptions—wrap them in domain-friendly errors.

## Testing Guidance
Use `pytest` plus temporary resources (tmp paths, in-memory databases) to exercise adapters end-to-end. Structure tests under `tests/<backend>/test_<operation>.py` and assert on both persisted data and protocol compliance. Include failure-case coverage (missing files, locked databases) to ensure graceful error handling.

## Commit & Review Expectations
Write imperative, ≤72-character subject lines (`Implement sqlite document store`). Pull requests must describe schema changes, migration steps, and verification results (`uv run pytest`). Provide notes on manual checks (e.g., `uv run python examples/list_tasks.py --storage sqlite`) when behaviour is user-facing.

## Architectural Notes
Stay aligned with the hexagonal design: adapters depend on `tasky-core` protocols but never on CLI or settings modules. Keep constructors decoupled from global state so composition roots (for example, the host CLI or service bootstrap) can instantiate repositories explicitly. Document wiring examples in those hosts and call out backend limitations so maintainers know when to add new implementations.
