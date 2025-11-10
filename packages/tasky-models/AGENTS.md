# Repository Guidelines

## Module Focus
`tasky-models` provides immutable domain representations for tasks, projects, and supporting value objects. Keep these classes side-effect free and limit them to validation, serialization, and simple computed properties. Business rules and orchestration live in the application layer, not here.

## Project Layout
All source lives in `src/tasky_models/`. Group related models inside submodules (`tasks.py`, `scheduling.py`, `identifiers.py`). Export the curated public API through `src/tasky_models/__init__.py` so downstream packages can rely on stable imports. Place shared constants or enums alongside the models they support.

## Development Commands
- `uv sync` synchronizes dependencies declared in this project.
- `uv run pytest` runs the model-focused tests (add `-k <pattern>` as needed).
- `uv run python -m tasky_models.inspect <model>` can host temporary validation scripts; remove exploratory modules after use.

## Coding Style & Conventions
Use Pydantic v2 base classes (`BaseModel`, `BaseSettings`) with `model_config = ConfigDict(frozen=True)` to enforce immutability where possible. Name models with clear intent (`TaskRecord`, `PriorityRule`). Keep field aliases explicit when they represent user-visible keys. Prefer `Enum` or `Literal` types for constrained fields and document complex invariants with docstrings.

## Testing Guidance
Adopt `pytest` with descriptive names (`test_task_record_default_status`). Cover edge cases such as invalid transitions, missing optional data, and serialization boundaries. When adding computed properties, ensure both positive and negative assertions exist. Use fixtures to share canonical task payloads across tests.

## Commit & Review Expectations
Subject lines stay imperative within 72 characters (`Introduce task priority enum`). Summaries should mention schema impacts so downstream packages can respond. Pull requests must outline migrations or back-compat concerns and list any regeneration steps (e.g., updating snapshots). Include `uv run pytest` in the verification section.

## Architectural Notes
Keep this package dependency-free beyond Pydantic. Avoid referencing adapters or services; instead, expose rich domain types that downstream layers can compose. When introducing breaking model changes, coordinate with `tasky-core` maintainers to stage updates safely across the clean architectural boundaries.
