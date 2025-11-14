# Tasks: Remove JSON Config Support

**Change ID**: `remove-json-config-support`
**Status**: Proposed

Each task below must be completed in order. Check each box only after the task and its validation steps are finished.

## Task Checklist

- [ ] **Task 1: Inventory all JSON references**
  - Run `rg -i "json" packages/ docs/ examples/` and note every usage tied to configuration loading, tests, or docs.
  - Record findings (file + purpose) inside the PR description or a scratch note so reviewers can verify coverage.
  - Validation: inventory document exists and no JSON reference is missed in later tasks.

- [ ] **Task 2: Remove JSON loading from tasky-projects**
  - Update `packages/tasky-projects/src/tasky_projects/config.py` so `ProjectConfig.from_file()` only considers `.tasky/config.toml`.
  - Delete any `_load_json` helpers, imports, and log messages tied to legacy conversion.
  - Validation: `uv run pytest packages/tasky-projects/tests/test_config.py -k config -v` passes.

- [ ] **Task 3: Remove JSON handling from tasky-settings sources**
  - Delete JSON detection branches from `packages/tasky-settings/src/tasky_settings/sources.py` (and related modules if present).
  - Ensure project settings sources raise the standard "Config file not found: .tasky/config.toml" error when TOML is absent.
  - Validation: `uv run pytest packages/tasky-settings/tests/test_sources.py -v` passes.

- [ ] **Task 4: Delete JSON-focused tests**
  - Remove or rewrite tests in `tasky-projects` and `tasky-settings` that exercised JSON fallback/migration.
  - Ensure remaining tests still provide ≥80% coverage (add TOML-only cases if gaps appear).
  - Validation: `uv run pytest --cov=packages --cov-fail-under=80` passes.

- [ ] **Task 5: Purge JSON references from documentation & examples**
  - Update docs, examples, and help text so only TOML configuration is described.
  - Add a release note / migration snippet pointing users to manual conversion steps.
  - Validation: `rg -i "config\.json"` in `docs/ examples/ packages/` returns zero results outside changelog history.

- [ ] **Task 6: Final verification**
  - Run `rg -i "json" packages/` and confirm only unrelated mentions (e.g., JSON output unrelated to config) remain.
  - Execute `uv run pytest` and `uv run ruff check --fix`.
  - Perform a CLI smoke test: `uv run tasky project init tmp-project` ensures `.tasky/config.toml` is created and no JSON paths are touched.
  - Validation: attach command transcripts to the PR and mark all boxes complete.
