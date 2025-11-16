# Change: Refactor Storage Backend Code Duplication

## Why

JSON and SQLite repositories contain significant duplicate code that violates the DRY principle:
- Both implement identical `_snapshot_to_task` methods with error handling
- Both use different serialization approaches (custom encoder vs Pydantic mode="json")
- Snapshot conversion logic is scattered across backends
- Changes to error handling must be duplicated across backends

This creates maintenance burden and risk of inconsistency between backends.

## What Changes

- Extract shared snapshot conversion logic to a common utility module
- Standardize serialization approach across both backends (use Pydantic mode="json")
- Remove duplicate error handling code
- Create a base class or mixin for common repository operations
- Ensure both backends remain behaviorally identical after refactoring

## Impact

- **Affected specs**: `task-storage`
- **Affected code**: `packages/tasky-storage/backends/json/repository.py`, `packages/tasky-storage/backends/sqlite/repository.py`, new `packages/tasky-storage/shared.py`
- **Backward compatibility**: Refactoring only; no API changes
- **Testing**: All existing tests must pass unchanged
