# Proposal: Standardize Project Configuration Format to TOML

**Change ID**: `standardize-config-format`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal standardizes project configuration storage to use TOML format exclusively, resolving user confusion caused by the current mix of JSON and TOML formats. Currently, `ProjectConfig` reads/writes JSON while `AppSettings` uses TOML, creating inconsistency in the codebase and confusion for users about which format to edit.

## Problem Statement

Users and developers face friction due to format inconsistency:
- **User Confusion**: When initializing projects with `tasky project init`, which format should they edit? Documentation becomes unclear when two formats exist.
- **Maintenance Burden**: Supporting both JSON and TOML formats doubles configuration complexity in code and tests.
- **Human-Friendliness Gap**: TOML is more human-friendly than JSON (comments, better readability), but only used for `AppSettings`, not project config.
- **Schema Sync Risk**: Keeping Pydantic models in sync across two serialization formats increases risk of inconsistency.

## Why

Task management projects benefit from standardization and consistency:

- **Single Format for Users**: Users work with one configuration format across all configuration levels (global and project), reducing cognitive load.
- **Improved Readability**: TOML comments allow users to document their project configuration inline.
- **Simplified Codebase**: One serialization format reduces code duplication in repository implementations.
- **Precedent**: `AppSettings` already established TOML as the project's configuration format; projects should follow the same pattern.
- **Backward Compatibility**: Detect legacy JSON files and auto-convert on first read, ensuring smooth migration.

## What Changes

- **ProjectConfig storage format**: From JSON to TOML
- **File format**: New projects create `.tasky/config.toml` (not `.tasky/config.json`)
- **Migration**: Legacy JSON files (`.tasky/config.json`) detected on read and auto-converted to TOML with a clear warning
- **from_file() method**: Updated to read TOML, with fallback to detect and convert legacy JSON
- **to_file() method**: Always writes TOML format
- **Pydantic model**: No changes to `ProjectConfig` model itself; only serialization/deserialization format changes

## Breaking Changes

- **BREAKING**: Code writing JSON configs directly will fail; must use new TOML approach
- Users with existing `.tasky/config.json` files will see a migration warning but functionality remains seamless

## Impact

- **Affected Specs**: `project-configuration`
- **Affected Code**:
  - `packages/tasky-projects/src/tasky_projects/models.py` - ProjectConfig.from_file() and to_file()
  - `packages/tasky-storage/` - JSON backend configuration handling
  - `packages/tasky-settings/` - Project configuration loading

## Acceptance Criteria

1. `ProjectConfig` reads and writes TOML files
2. Legacy JSON files detected and auto-converted on read
3. Auto-conversion logs clear warning message
4. New projects always initialize with TOML
5. Pydantic model validation remains unchanged
6. All tests pass with new format
7. Migration is transparent to end users

## Non-Goals

- Changing the Pydantic model structure
- Removing JSON support from AppSettings
- Changing file location or directory structure
- Implementing validation schema changes

## Related Specs

- `project-configuration` (MODIFIED)
- `global-configuration` (no changes, already TOML)

## Risks and Mitigations

**Risk**: Users with existing JSON configs may be surprised by migration warning
**Mitigation**: Warning message is clear and non-blocking; functionality continues seamlessly

**Risk**: Tooling expecting JSON format breaks
**Mitigation**: Only internal code affected; auto-conversion ensures no manual user intervention

**Risk**: Incomplete JSON migration leaves orphaned files
**Mitigation**: Both formats coexist; JSON files are auto-converted but not deleted (safe cleanup)

## Migration Plan

1. Implement TOML reading/writing in ProjectConfig
2. Add JSON detection and auto-conversion with warning
3. Update all backend storage adapters
4. Run full test suite
5. Users with JSON configs see warning on first read, file auto-converts to TOML on write

## Alternatives Considered

1. **Keep both formats**: Rejected (ongoing maintenance burden, user confusion)
2. **Migrate to JSON everywhere**: Rejected (TOML more user-friendly, AppSettings already uses TOML)
3. **Create custom migration tool**: Rejected (auto-conversion on read is simpler and more reliable)
