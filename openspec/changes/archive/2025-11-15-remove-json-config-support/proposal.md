# Proposal: Remove JSON Config Support

**Change ID**: `remove-json-config-support`
**Status**: Proposed
**Created**: 2025-11-14
**Author**: AI Assistant

## Overview

This proposal removes legacy JSON configuration format support. The project transitioned from JSON to TOML during the `standardize-config-format` change, with JSON support maintained for backwards compatibility. This change can be executed at any time to simplify the codebase by removing dual-format support, consolidating on TOML exclusively.

## Problem Statement

Supporting both JSON and TOML configuration formats creates:

- **Code Duplication**: Multiple code paths for JSON vs TOML loading/detection in `tasky-projects` and `tasky-settings`
- **Test Burden**: Legacy JSON test cases represent ~15-20% of configuration tests but provide decreasing value
- **Cognitive Load**: Future developers must understand why JSON support exists and maintenance paths
- **Maintenance Risk**: Changes to configuration logic must account for both formats, increasing bug surface
- **Decision Flexibility**: Current implementation carries JSON support without a clear removal timeline

## Why

Removing dual-format support simplifies the codebase while maintaining the option to defer:

- **Cleaner Codebase**: Removing ~100-150 lines of JSON-specific handling and ~12-15 test cases simplifies logic
- **Reduced Complexity**: Single code path for TOML eliminates branching and edge cases
- **Lower Maintenance**: Future configuration changes only need to consider one format
- **Flexible Timeline**: Can be executed now or deferred; no lock-in to major version boundaries
- **Reversible Decision**: If JSON support becomes necessary again, it can be re-added with clear rationale

## What Changes

- **Remove JSON detection logic**: No more checking for `.tasky/config.json` in `ProjectConfig.from_file()`
- **Remove JSON migration warnings**: Migration warnings logged during v1.0 cycle are no longer needed
- **Remove `_load_json()` method**: JSON-specific deserialization method in `tasky-projects/config.py`
- **Remove JSON source handling**: Legacy JSON source detection in `tasky-settings/sources.py`
- **Remove JSON test cases**: All `test_*_json_*()` and `test_*_legacy_*()` tests in test suite
- **Update documentation**: Mark JSON support as removed in changelog and migration guide

## Breaking Changes

- **BREAKING**: Attempting to use old `.tasky/config.json` files will fail with clear error message directing to TOML format
- Users must manually convert legacy JSON configs to TOML (simple rename and format update)

## Impact

- **Affected Specs**: `project-configuration`
- **Affected Code**:
  - `packages/tasky-projects/src/tasky_projects/config.py` - ProjectConfig.from_file() (JSON detection removed)
  - `packages/tasky-settings/src/tasky_settings/sources.py` - ProjectConfigSource._load_config() (JSON detection removed)
  - `packages/tasky-projects/tests/test_config.py` - Remove JSON-related test cases (~8-10 tests)
  - `packages/tasky-settings/tests/test_sources.py` - Remove JSON-related test cases (~4-6 tests)
  - Documentation files mentioning JSON migration

## Acceptance Criteria

1. All JSON detection and loading code is removed from configuration system
2. No references to `.tasky/config.json` remain in production code
3. All JSON-specific test cases are deleted
4. Migration warnings and JSON-to-TOML conversion code is removed
5. `ProjectConfig.from_file()` only attempts TOML loading
6. All tests pass (with reduced count due to removed JSON tests)
7. Code coverage remains ≥80%
8. Changelog documents breaking change and migration path

## Non-Goals

- Changing TOML configuration structure or format
- Removing TOML support (obviously)
- Removing any other deprecated features
- Pre-v1.0 changes

## Related Specs

- `project-configuration` (MODIFIED - remove JSON fallback requirement)
- `standardize-config-format` (predecessor change, reference for context)

## Risks and Mitigations

**Risk**: Users with existing JSON configs lose a working feature
**Mitigation**: Clear **release notes** (not in-code messages) document breaking change and migration steps. TOML conversion is trivial (rename + format update).

**Risk**: Incomplete removal leaves orphaned JSON-related code
**Mitigation**: Comprehensive audit (Task 1) finds ALL JSON references; code review validates 100% clean TOML-only implementation. Any leftover JSON code = rejection.

**Risk**: Code contains stray JSON references, comments, or deprecation paths
**Mitigation**: Post-removal validation searches entire codebase for "json", "JSON", "legacy", "deprecated" in configuration code. Zero tolerance for any traces.

## User Experience After Removal

When JSON support is removed, users with `.tasky/config.json` files will experience:

```
Error: Config file not found: .tasky/config.toml
```

No deprecation warnings, no special handling, no migration messages. The code will be **100% clean** as if TOML was always the only format. Users upgrading from earlier versions with JSON configs must:

1. Rename the file: `mv .tasky/config.json .tasky/config.toml`
2. Convert the format from JSON to TOML syntax (refer to [TOML documentation](https://toml.io))
3. Retry their command

This is documented in **release notes** (not in code), with a clear breaking change notice and example migration instructions. After that, the code contains zero references to JSON, legacy formats, or backwards compatibility paths.

## Alternatives Considered

1. **Keep JSON support indefinitely**: Ongoing maintenance burden, code complexity
2. **Add automatic migration tool**: Nice-to-have but adds complexity; manual migration is simple enough
3. **Provide backwards compatibility layer**: Negates purpose of cleanup

## Decision Timeline (Flexible)

This change can be scheduled at team discretion:

- **Option A** (Soon): Execute immediately if codebase is ready; no need to carry JSON support longer
- **Option B** (Planned): Schedule for next major release (v2.0) to bundle breaking changes
- **Option C** (Deferred): Keep JSON support if decided to maintain broader backwards compatibility

The change is **not locked** to any specific release—decide when it makes sense.

## Implementation Notes

When implementing this change, ensure:

1. **Search comprehensively**: Use `rg "json|JSON"` to find all related code
2. **Code may have evolved**: Since this spec is written now, verify all JSON code paths before removal:
   - Check `ProjectConfig.from_file()` implementation details
   - Check `tasky-settings` config loading implementation
   - Check for any new JSON utility functions that may have been added
   - Check for JSON references in imports, comments, examples, and docs

3. **Test comprehensively**: Run full test suite multiple times; ensure no JSON code paths are accidentally exercised
4. **Verify migration path**: Ensure TOML-only code paths work correctly in isolation
5. **Update all docs**: Changelog, error messages, examples, and migration guides

## Specification Impact Summary

| Spec | Current State | After Change |
|------|---|---|
| `project-configuration` | Supports JSON (legacy) and TOML | TOML only |
| Global configuration | TOML only | TOML only (no change) |
