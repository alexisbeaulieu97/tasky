# Implementation Tasks: Align tasky-projects Package to Use TOML Format

This document outlines the ordered implementation tasks for aligning `ProjectConfig` to use TOML format for file I/O, matching the system-wide configuration format.

## Task Checklist

### Phase 1: Update Imports and from_file() Method

- [ ] **Task 1.1**: Update import statements in config.py
  - Open `packages/tasky-projects/src/tasky_projects/config.py`
  - Replace `import json` with `import tomllib`
  - Add `import tomli_w` for write operations
  - **Validation**: Code type-checks successfully

- [ ] **Task 1.2**: Update from_file() to read TOML
  - Locate `ProjectConfig.from_file()` method in `packages/tasky-projects/src/tasky_projects/config.py`
  - Replace `json.load(f)` with `tomllib.load(f)`
  - Change file open mode from `"r"` to `"rb"` (TOML requires binary mode)
  - Remove `encoding="utf-8"` parameter (not needed for binary mode)
  - **Validation**: Code type-checks successfully

- [ ] **Task 1.3**: Update from_file() docstring
  - Change docstring from "Load configuration from a JSON file" to "Load configuration from a TOML file"
  - Update any JSON references in docstring to TOML
  - **Validation**: Docstring accurately describes method behavior

### Phase 2: Update to_file() Method

- [ ] **Task 2.1**: Update to_file() to write TOML
  - Locate `ProjectConfig.to_file()` method in `packages/tasky-projects/src/tasky_projects/config.py`
  - Replace `f.write(self.model_dump_json(indent=2))` with `tomli_w.dump(self.model_dump(), f)`
  - Change file open mode from `"w"` to `"wb"` (TOML requires binary mode)
  - Remove `encoding="utf-8"` parameter (not needed for binary mode)
  - **Validation**: Code type-checks successfully

- [ ] **Task 2.2**: Update to_file() docstring
  - Change docstring from "Save configuration to a JSON file" to "Save configuration to a TOML file"
  - Update any JSON references in docstring to TOML
  - **Validation**: Docstring accurately describes method behavior

### Phase 3: Update Tests

- [ ] **Task 3.1**: Update test imports
  - Open `packages/tasky-projects/tests/test_config.py`
  - Replace `import json` with `import tomllib` and `import tomli_w`
  - **Validation**: Test file imports successfully

- [ ] **Task 3.2**: Update test file extensions and format expectations
  - Change all `config.json` references to `config.toml`
  - Update test data format from JSON to TOML syntax
  - For example: `test_project_config_from_file_valid` should write TOML, not JSON
  - Update `test_project_config_from_file_invalid_json` to test invalid TOML (rename to `test_project_config_from_file_invalid_toml`)
  - Update `test_project_config_to_file_pretty_printed` to verify TOML formatting instead of JSON
  - **Validation**: Code type-checks successfully

- [ ] **Task 3.3**: Update test assertions for TOML format
  - Change assertions that read files to use `tomllib.load()` instead of `json.loads()`
  - Update format expectations (TOML uses sections like `[storage]` instead of nested JSON)
  - Verify `test_project_config_round_trip` works with TOML serialization
  - **Validation**: Assertions match TOML format expectations

### Phase 4: Validation and Testing

- [ ] **Task 4.1**: Run unit tests for tasky-projects
  - Execute: `uv run pytest packages/tasky-projects/tests/test_config.py -v`
  - Verify all tests pass
  - Address any failures related to TOML format differences
  - **Validation**: All tests pass

- [ ] **Task 4.2**: Run full test suite
  - Execute: `uv run pytest`
  - Verify no regressions in other packages
  - Confirm round-trip test (save → load) preserves data accurately
  - **Validation**: All tests pass

- [ ] **Task 4.3**: Manual verification of TOML output
  - Create a temporary test that writes a `ProjectConfig` to file
  - Inspect the output file to verify valid TOML format
  - Verify sections (`[storage]`), datetime format, and readability
  - **Validation**: Output file is valid, human-readable TOML

### Phase 5: Code Quality

- [ ] **Task 5.1**: Run code quality checks
  - Execute: `uv run ruff check --fix`
  - Execute: `uv run ruff format`
  - Address any linting issues
  - **Validation**: No linting errors

- [ ] **Task 5.2**: Type checking
  - Verify `tomllib` and `tomli_w` type stubs are available
  - Run type checker if configured
  - Ensure no type errors introduced
  - **Validation**: Type checking passes

## Notes

- **Sequential Dependencies**: Tasks should be completed in order within each phase
- **Testing Strategy**: Unit tests validate each layer (from_file, to_file, round-trip)
- **Rollback**: Each task is independently reversible if issues arise
- **Python Version**: `tomllib` is Python 3.11+ standard library (project targets ≥3.13)
- **Binary Mode**: TOML parsers require binary file mode (`"rb"` and `"wb"`)

## TOML Format Example

After changes, `ProjectConfig.to_file()` will produce files like:

```toml
version = "1.0"
created_at = "2025-11-12T10:00:00Z"

[storage]
backend = "json"
path = "tasks.json"
```

## Test Data Example

Test files will use TOML format:

```toml
version = "1.0"
created_at = "2025-11-12T10:00:00Z"

[storage]
backend = "json"
path = "tasks.json"
```

## Estimated Duration

- Phase 1: 10 minutes
- Phase 2: 5 minutes
- Phase 3: 10 minutes
- Phase 4: 5 minutes
- Phase 5: 5 minutes

**Total**: ~35 minutes (within 0.5-hour estimate)
