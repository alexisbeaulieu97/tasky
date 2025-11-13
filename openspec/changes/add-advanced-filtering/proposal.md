# Change: Add Advanced Task Filtering

**Change ID**: `add-advanced-filtering`
**Status**: Proposal
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal extends task filtering capabilities beyond status-based filtering to include date range filtering and text search. Currently, users can only filter by status. This change adds two new powerful filtering dimensions—temporal filtering by task creation date and content search—while maintaining AND logic for combining multiple criteria.

## Problem Statement

The current status-only filtering (`--status pending`) is useful but insufficient for real-world task management. Users need to:
1. Find recently created tasks (`--created-after 2025-01-01`)
2. Find tasks created in a specific period (`--created-before 2025-12-31`)
3. Search tasks by name or description (`--search "fix bug"`)
4. Combine filters to refine results (`--status pending --created-after 2025-11-01 --search "urgent"`)

Without these capabilities, users managing hundreds of tasks struggle to locate specific work. The inability to combine filter criteria makes the system less useful as task volume grows.

## Why

Advanced filtering addresses critical usability gaps:

- **Time-based Focus**: Developers want to see tasks from the current week/month without manually parsing timestamps
- **Content Search**: Users need to find tasks mentioning specific keywords or problem descriptions
- **Combined Criteria**: Real-world workflows require multiple filters (e.g., "pending tasks from this month mentioning 'bug'")

The implementation is straightforward:
- Date parsing using Python's `datetime.fromisoformat()` for ISO 8601 compliance
- Case-insensitive substring search in task name and details
- AND logic combining all criteria (all must match)
- Clean CLI UX with helpful error messages for invalid dates

## What Changes

Add advanced filtering at three layers:

1. **Domain Model**: Introduce `TaskFilter` model in `tasky-tasks` with composable criteria
2. **Repository Protocol**: Extend `TaskRepository` with `find_tasks(filter: TaskFilter)` method
3. **JSON Backend**: Implement in-memory filtering with date range and text search
4. **Service Layer**: Add convenience method `find_tasks(filter: TaskFilter)` to `TaskService`
5. **CLI**: Add `--created-after`, `--created-before`, and `--search` options to `task list` command
6. **CLI Error Handling**: Provide helpful error messages for invalid date formats

### User-Facing Changes

```bash
# List all tasks (existing behavior)
tasky task list

# Filter by status only (existing behavior)
tasky task list --status pending

# Filter by date range
tasky task list --created-after 2025-01-01
tasky task list --created-before 2025-12-31
tasky task list --created-after 2025-11-01 --created-before 2025-11-30

# Filter by text search (case-insensitive, searches name and details)
tasky task list --search "bug fix"

# Combine criteria with AND logic
tasky task list --status pending --created-after 2025-11-01
tasky task list --status pending --search "urgent"
tasky task list --status pending --created-after 2025-11-01 --search "bug fix"
```

## Acceptance Criteria

1. `TaskFilter` model defined in `tasky-tasks` with `statuses`, `created_after`, `created_before`, `name_contains` fields
2. Repository protocol includes `find_tasks(filter: TaskFilter)` method
3. `TaskService` provides `find_tasks(filter: TaskFilter)` method
4. JSON backend implements date range and text search filtering
5. CLI supports `--created-after`, `--created-before`, `--search` options
6. Invalid date formats (non-ISO 8601) show helpful error messages
7. Search is case-insensitive
8. Multiple criteria are combined using AND logic (all must match)
9. Test coverage ≥80% for all new functionality

## Non-Goals

- **Regular expression search**: Basic substring search only
- **Date parsing flexibility**: ISO 8601 format only (`YYYY-MM-DD`)
- **Time-of-day filtering**: Date-only, no time component
- **Database optimization**: Future work for SQLite/Postgres backends
- **Complex query DSL**: No filter composition language

## Dependencies

This change depends on:
- `add-automatic-timestamps` (for `created_at` field)
- `add-task-state-transitions` (for `TaskStatus` enum)
- `add-task-filtering` (for status filtering foundation)

## Risks and Mitigations

**Risk**: Date parsing errors with non-ISO 8601 formats
**Mitigation**: Require ISO 8601 format (`YYYY-MM-DD`), validate at CLI layer, show helpful error message with example format.

**Risk**: Text search on large task lists may be slow
**Mitigation**: Current in-memory search is O(n*m) where n=tasks and m=avg search string length. Acceptable for <10,000 tasks. Future database backends can optimize with indexed search.

**Risk**: AND logic may be too restrictive for some use cases
**Mitigation**: AND logic is intuitive and matches user expectations. Future enhancement can add OR logic if needed, but current simple approach is sufficient.

## Alternatives Considered

1. **OR logic instead of AND**: Rejected because AND is more intuitive for filtering. Users expect all criteria to match.
2. **Support partial date matching (month, year)**: Rejected as over-engineering. ISO 8601 full dates are standard and clear.
3. **Full regex search**: Rejected as over-complexity. Substring search covers 95% of use cases.

## Implementation Notes

- Keep filtering logic simple and testable
- Validate dates at CLI before calling service
- Ensure case-insensitive search (convert to lowercase for comparison)
- AND logic: all non-null criteria must match
- Return empty list when no tasks match (don't error)
- Document the filtering behavior clearly for future extensions

## Related Changes

- Foundation extends `add-task-filtering` (status filtering only)
- Enables future rich query capabilities (sorting, pagination, etc.)
- Supports future database query optimization with indexed search
- Establishes `TaskFilter` pattern for future extension

## Impact

**Affected specs**:
- `task-cli-operations` (modified to add new filter requirements)

**Affected code**:
- `packages/tasky-tasks/src/tasky_tasks/models.py` (add `TaskFilter`)
- `packages/tasky-tasks/src/tasky_tasks/ports.py` (extend `TaskRepository` protocol)
- `packages/tasky-tasks/src/tasky_tasks/service.py` (add `find_tasks()` method)
- `packages/tasky-storage/src/tasky_storage/backends/json/repository.py` (implement filtering)
- `packages/tasky-cli/src/tasky_cli/commands/tasks.py` (add CLI options)

## Timeline

Estimated implementation: 3-4 hours

- Phase 1: Model & Protocol (30 min)
- Phase 2: Service Layer (30 min)
- Phase 3: JSON Backend (45 min)
- Phase 4: CLI Integration (45 min)
- Phase 5: Testing & Validation (30 min)
