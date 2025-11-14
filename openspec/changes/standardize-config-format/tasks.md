# Implementation Tasks: Standardize Project Configuration Format to TOML

This document outlines the ordered implementation tasks for standardizing project configuration to use TOML format exclusively. Tasks deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: ProjectConfig Model Updates (Foundation)

- [x] **Task 1.1**: Update `ProjectConfig` model to support TOML serialization
  - Update `packages/tasky-projects/src/tasky_projects/models.py`
  - Ensure Pydantic model works with TOML deserialization (no structural changes needed)
  - Add helper methods for TOML parsing if needed
  - **Validation**: Model type-checks successfully

- [x] **Task 1.2**: Implement TOML reading in `ProjectConfig.from_file()`
  - Update `packages/tasky-projects/src/tasky_projects/models.py` (or appropriate module)
  - Implement logic to read `.tasky/config.toml` using `tomli` library
  - Add fallback detection for legacy `.tasky/config.json` files
  - Log warning when legacy JSON is detected
  - Return parsed configuration as `ProjectConfig` instance
  - **Validation**: Code compiles and type-checks

- [x] **Task 1.3**: Implement TOML writing in `ProjectConfig.to_file()`
  - Implement logic to write ProjectConfig to TOML format using `tomli_w` library
  - Always write to `.tasky/config.toml` (TOML format)
  - Create `.tasky/` directory if it doesn't exist
  - Set appropriate file permissions (user read/write only)
  - **Validation**: Code compiles and type-checks

- [x] **Task 1.4**: Write unit tests for ProjectConfig TOML operations
  - Create `packages/tasky-projects/tests/test_project_config_toml.py`
  - Test reading valid TOML config file
  - Test reading and deserializing to ProjectConfig instance
  - Test invalid TOML reporting clear errors
  - Test to_file() writes valid TOML
  - Test from_file() and to_file() round-trip correctly
  - **Validation**: Run `uv run pytest packages/tasky-projects/tests/test_project_config_toml.py -v`

### Phase 2: Legacy JSON Migration

- [x] **Task 2.1**: Implement JSON detection and auto-conversion logic
  - Update `ProjectConfig.from_file()` to detect `.tasky/config.json` when `.tasky/config.toml` missing
  - Load JSON file using standard `json` library
  - Log clear warning: "Legacy JSON config detected at {path}, will migrate to TOML format on next write"
  - Parse JSON to ProjectConfig instance
  - Return the loaded configuration (transparent to caller)
  - **Validation**: Code compiles and type-checks

- [x] **Task 2.2**: Implement auto-write of TOML on first write after migration detection
  - When ProjectConfig with migrated JSON is written via `to_file()`, write as TOML
  - Legacy JSON file remains (safe, no deletion of user files)
  - Next read will find TOML and use it
  - **Validation**: Code compiles and type-checks

- [x] **Task 2.3**: Write migration tests
  - Create `packages/tasky-projects/tests/test_project_config_migration.py`
  - Test detecting legacy JSON config when TOML missing
  - Test warning message is logged
  - Test reading legacy JSON and converting to ProjectConfig
  - Test writing previously-migrated config as TOML
  - Test both JSON and TOML coexist during transition
  - **Validation**: Run `uv run pytest packages/tasky-projects/tests/test_project_config_migration.py -v`

### Phase 3: Storage Adapter Updates

- [x] **Task 3.1**: Update JSON backend storage adapter to use new ProjectConfig TOML methods
  - Update `packages/tasky-storage/src/tasky_storage/backends/json/` (or appropriate backend)
  - Use `ProjectConfig.from_file()` for reading (now reads TOML with JSON fallback)
  - Use `ProjectConfig.to_file()` for writing (now writes TOML)
  - Remove any direct JSON serialization code for ProjectConfig
  - **Validation**: Code compiles and type-checks

- [x] **Task 3.2**: Update storage tests to verify TOML format
  - Update `packages/tasky-storage/tests/` to validate TOML format
  - Verify written config files are TOML (not JSON)
  - Test legacy JSON detection in storage layer
  - **Validation**: Run `uv run pytest packages/tasky-storage/tests/ -v`

### Phase 4: Settings and Initialization

- [x] **Task 4.1**: Verify `tasky project init` creates TOML config
  - Check `packages/tasky-projects/src/tasky_projects/` project initialization logic
  - Ensure new projects create `.tasky/config.toml` (not `.tasky/config.json`)
  - Initialize with sensible defaults
  - **Validation**: Run `uv run tasky project init` and verify `.tasky/config.toml` created

- [x] **Task 4.2**: Update project settings loading in `tasky-settings`
  - Update `packages/tasky-settings/` to load ProjectConfig using new TOML methods
  - Ensure fallback to JSON works transparently
  - **Validation**: Code compiles and type-checks

### Phase 5: CLI and Integration

- [x] **Task 5.1**: Test `tasky project init` creates TOML format
  - Manual test: `uv run tasky project init`
  - Verify `.tasky/config.toml` is created
  - Verify content is valid TOML
  - **Validation**: Manual verification

- [x] **Task 5.2**: Write integration tests for TOML config workflow
  - Create `packages/tasky-cli/tests/test_project_config_toml.py`
  - Test full workflow: init → modify → reload config
  - Test config overrides work correctly
  - **Validation**: Run `uv run pytest packages/tasky-cli/tests/test_project_config_toml.py -v`

### Phase 6: Backward Compatibility Verification

- [x] **Task 6.1**: Test legacy JSON config still works (with warning)
  - Create temporary project with `.tasky/config.json` (legacy format)
  - Run commands and verify they work
  - Verify warning message is logged
  - **Validation**: Manual test produces expected warning

- [x] **Task 6.2**: Test migration pathway: JSON → TOML
  - Create project with `.tasky/config.json`
  - Run a command (reads JSON, logs warning)
  - Modify config (triggers write)
  - Verify `.tasky/config.toml` now exists
  - Verify JSON file still exists (safe cleanup)
  - **Validation**: Manual verification of migration

### Phase 7: Testing and Documentation

- [x] **Task 7.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage
  - **Validation**: All tests pass

- [x] **Task 7.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - **Validation**: Code passes all quality checks

- [x] **Task 7.3**: Update documentation and comments
  - Add inline comments explaining TOML format choice
  - Document migration behavior for developers
  - Update any references to JSON config format
  - **Validation**: Documentation is clear and accurate

## Notes

- **Dependencies**: Phases must be completed sequentially
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Rollback**: Each task is independently reversible if issues arise
- **Python Dependencies**: May need to add `tomli` and `tomli_w` to `pyproject.toml` if not already present

## Estimated Duration

- Phase 1: 1 hour
- Phase 2: 1 hour
- Phase 3: 45 minutes
- Phase 4: 45 minutes
- Phase 5: 1 hour
- Phase 6: 45 minutes
- Phase 7: 1 hour

**Total**: ~6-7 hours
