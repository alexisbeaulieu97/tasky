# Proposal: Align tasky-projects Package to Use TOML Format

**Change ID**: `align-tasky-projects-format`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant
**Phase**: 4.4 (Quick alignment fix, ~0.5 hours)
**Depends On**: Phase 4.2 (`standardize-config-format`)

## Overview

This proposal aligns the `tasky-projects` package's `ProjectConfig` class to use TOML format for file I/O, matching the system-wide configuration format established in Phase 4.2. Currently, `ProjectConfig.from_file()` and `ProjectConfig.to_file()` use JSON serialization, creating a mismatch with the TOML-based configuration system used by `tasky-settings`.

## Problem Statement

The `tasky-projects` package has an internal format mismatch:

- **System Reality**: The settings layer (`tasky-settings/sources.py`) reads `.tasky/config.toml` using `tomllib`
- **Package Reality**: The `ProjectConfig` class in `tasky-projects/config.py` reads/writes JSON using the `json` module
- **User Impact**: The `ProjectConfig` helper methods can't be used to represent real project files, forcing code duplication
- **Technical Debt**: Phase 4.2 standardized the format system-wide, but `tasky-projects` wasn't updated

This is a straightforward alignment task to make `ProjectConfig` consistent with the rest of the system.

## Why

Aligning `ProjectConfig` to use TOML provides immediate benefits:

- **Format Consistency**: All configuration code uses TOML, matching system expectations
- **Code Reuse**: `ProjectConfig` methods can be used throughout the codebase without format workarounds
- **Developer Clarity**: No confusion about which format a given config class uses
- **Testing Accuracy**: Tests using `ProjectConfig` helper methods will match real file formats
- **Minimal Effort**: This is a small, focused change (estimated 0.5 hours) with clear scope

## What Changes

- **Import statements**: Replace `import json` with `import tomllib` and `import tomli_w`
- **from_file() method**: Read TOML using `tomllib.load()` instead of `json.load()`
- **to_file() method**: Write TOML using `tomli_w.dump()` instead of `model_dump_json()`
- **Docstrings**: Update method docstrings to reference "TOML file" instead of "JSON file"
- **File extension**: No change to file paths (already `.tasky/config.toml` in system)
- **Tests**: Update test file to use TOML format expectations

## Breaking Changes

None. This is an internal alignment fix:

- The system already uses TOML (`.tasky/config.toml`)
- `ProjectConfig` methods are internal helpers, not public API
- Tests are the only consumer of these methods currently

## Impact

- **Affected Specs**: `project-configuration` (minor update to clarify TOML usage)
- **Affected Code**:
  - `packages/tasky-projects/src/tasky_projects/config.py` - ProjectConfig class methods
  - `packages/tasky-projects/tests/test_config.py` - Update test expectations from JSON to TOML

## Acceptance Criteria

1. `ProjectConfig.from_file()` successfully reads TOML files
2. `ProjectConfig.to_file()` successfully writes TOML files
3. Round-trip test (save → load) preserves all data accurately
4. Docstrings correctly reference TOML format
5. Import statements use `tomllib` (read) and `tomli_w` (write)
6. All existing tests pass with TOML format
7. No regression in Pydantic model validation

## Non-Goals

- Changing the Pydantic model structure or field definitions
- Adding JSON migration or backward compatibility (system already migrated in Phase 4.2)
- Modifying file paths or directory structure
- Changing how `tasky-settings` loads configuration
- Adding new configuration fields or validation

## Related Specs

- `project-configuration` (MODIFIED - clarify TOML serialization)

## Risks and Mitigations

**Risk**: `tomllib` is Python 3.11+ standard library
**Mitigation**: Project targets Python ≥3.13 per CLAUDE.md, so this is not a concern

**Risk**: TOML serialization may handle datetime differently than JSON
**Mitigation**: Pydantic's model validation handles datetime consistently; round-trip test validates this

**Risk**: Breaking tests that expect JSON format
**Mitigation**: Tests are easy to update; this is caught immediately in test suite

## Migration Plan

1. Update imports in `config.py` (replace `json` with `tomllib` and `tomli_w`)
2. Update `from_file()` to read TOML with `tomllib.load()`
3. Update `to_file()` to write TOML with `tomli_w.dump()`
4. Update docstrings to reference TOML
5. Update test file to expect TOML format and syntax
6. Run test suite to validate changes
7. Verify round-trip test passes with TOML

## Alternatives Considered

1. **Keep JSON in ProjectConfig**: Rejected - perpetuates format mismatch and code duplication
2. **Support both formats**: Rejected - unnecessary complexity for an internal helper class
3. **Remove helper methods entirely**: Rejected - methods provide useful abstraction for tests and future code

## Estimated Duration

**~0.5 hours** (30 minutes)
- Code changes: 15 minutes
- Test updates: 10 minutes
- Validation: 5 minutes
