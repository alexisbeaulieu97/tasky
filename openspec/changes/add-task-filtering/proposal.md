# Proposal: Add Task Filtering and Querying

**Change ID**: `add-task-filtering`  
**Status**: Draft  
**Created**: 2025-11-11  
**Author**: AI Assistant

## Overview

This proposal introduces task filtering capabilities to allow users to query tasks by status. Currently, users can only retrieve all tasks via `tasky task list`, which becomes unwieldy as the task count grows. This change adds status-based filtering to improve usability and lays the foundation for future rich querying features.

## Problem Statement

Users cannot efficiently view subsets of their tasks based on status. When managing many tasks, seeing all tasks at once makes it difficult to focus on relevant work. Users need to filter tasks to view only:
- Pending tasks (active work)
- Completed tasks (done items)
- Cancelled tasks (abandoned items)

## Why

Task filtering is essential for usability in any task management system. As projects grow beyond a handful of tasks, users need to focus on specific subsets:

- **Focus on Active Work**: Developers want to see only pending tasks when planning their day
- **Review Completed Work**: Users need to review what has been accomplished without clutter from pending items
- **Audit Cancelled Tasks**: Understanding what was abandoned helps with project retrospectives

Without filtering, users must mentally parse large lists to find relevant tasks, leading to decreased productivity and increased cognitive load. This change addresses the most common filtering need (status) while establishing patterns for future rich querying capabilities.

The implementation is straightforward (O(n) in-memory filtering for JSON backend) and provides immediate value without over-engineering. Future database backends can optimize with indexed queries when needed.

## Proposed Solution

Add status filtering at four layers:

1. **Repository Protocol**: Extend `TaskRepository` with `get_tasks_by_status(status: TaskStatus)` method
2. **JSON Backend**: Implement in-memory filtering in `JsonTaskRepository`
3. **Service Layer**: Add convenience methods (`get_pending_tasks()`, `get_completed_tasks()`, `get_cancelled_tasks()`)
4. **CLI**: Add `--status` option to `tasky task list` command

### User-Facing Changes

```bash
# List all tasks (existing behavior)
tasky task list

# List only pending tasks
tasky task list --status pending

# List completed tasks (short form)
tasky task list -s completed

# List cancelled tasks
tasky task list --status cancelled
```

## Acceptance Criteria

1. Repository protocol includes `get_tasks_by_status(status: TaskStatus)` method
2. Service provides convenience methods: `get_pending_tasks()`, `get_completed_tasks()`, `get_cancelled_tasks()`
3. JSON backend implements in-memory filtering correctly
4. CLI supports `--status/-s` option with validation
5. Invalid status values show helpful error messages
6. Filtering returns results instantly for 1000+ tasks
7. Test coverage ≥80% for all new functionality

## Non-Goals

- Date range filtering (future enhancement)
- Text search in name/details (future enhancement)
- Combining multiple filter criteria (future enhancement)
- Database query optimization (SQLite/Postgres not yet implemented)
- Rich query DSL or filter composition

## Dependencies

This change depends on:
- `add-automatic-timestamps` (for consistent task state)
- `add-task-state-transitions` (for TaskStatus enum and state management)
- `add-domain-exception-hierarchy` (for proper error handling)

## Risks and Mitigations

**Risk**: In-memory filtering may be slow for large task counts  
**Mitigation**: JSON backend filtering is O(n) and acceptable for <10,000 tasks. Future database backends can optimize with indexed queries.

**Risk**: Adding filtering now might conflict with future rich query features  
**Mitigation**: Design uses single-parameter filtering as building block. Future `find_tasks(filter: TaskFilter)` method can handle complex queries without breaking existing code.

## Alternatives Considered

1. **Implement full query DSL immediately**: Rejected as over-engineering for current needs
2. **Add filtering only to service layer**: Rejected because it limits backend optimization opportunities
3. **Use string-based status parameter**: Rejected in favor of type-safe `TaskStatus` enum

## Implementation Notes

- Keep filtering logic simple and testable
- Ensure backend implementations remain stateless
- Validate status parameter in CLI before calling service
- Document the filtering behavior clearly for future rich query work

## Related Changes

- Foundation for future `find_tasks(filter: TaskFilter)` capability
- Supports future SQL query optimization in database backends
- Enables future filtering combinations (status + date range + text search)
