# Change: Improve Performance and Data Safety

## Why

The codebase has several performance and reliability issues that can impact users:
- JSON backend has N+1 pattern: converts all tasks to TaskModel before filtering
- JSON backend lacks atomic writes: partial writes on disk-full can corrupt files
- SQLite has unbounded registry growth: loading 100k+ projects into RAM
- Broad exception catching in import/export masks genuine bugs
- Registry name collision handler silently fails without diagnostics

These issues create risk of data loss, poor performance on large datasets, and hidden bugs during debugging.

## What Changes

- Implement filter-first strategy in JSON backend (filter snapshots before expensive model conversion)
- Add atomic writes for JSON storage (temp file + atomic rename)
- Add size limits and pagination for project registry
- Narrow exception handling in import/export to catch specific errors
- Improve error diagnostics in registry name disambiguation
- Add comprehensive logging for debugging

## Impact

- **Affected specs**: `task-storage`, `project-registry-capability`, `task-import-capability`
- **Affected code**: `packages/tasky-storage/`, `packages/tasky-projects/registry.py`, `packages/tasky-tasks/export.py`
- **Backward compatibility**: No breaking changes; performance and reliability improvements only
- **User impact**: Faster filtering, data protection, better error visibility
