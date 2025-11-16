# Change: Improve Storage Backend Testing Coverage

## Why

The SQLite storage backend has only 54% test coverage with 69 uncovered statements, while error paths (database failures, integrity violations, concurrency) are largely untested. Additionally, there are no integration tests validating backend switching or data integrity across migrations. This creates a high risk of production failures and data loss when users migrate between backends or encounter database errors.

## What Changes

- Expand SQLite repository tests to achieve ≥80% coverage
- Add comprehensive error path testing (database errors, integrity violations, lock contention)
- Create integration tests for backend migration scenarios
- Add concurrency and stress tests for SQLite WAL mode
- Add corruption recovery tests for registry service
- Ensure JSON and SQLite backends are behaviorally identical

## Impact

- **Affected specs**: `task-storage`, `project-registry-capability`
- **Affected code**: `packages/tasky-storage/tests/`, `packages/tasky-projects/tests/`
- **Backward compatibility**: Testing only; no API changes
- **Risk mitigation**: Validates critical data-loss scenarios
