# Proposal: Add Task Show Command

**Change ID**: `add-task-show-command`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal introduces the `tasky task show TASK_ID` CLI command to enable users to view the full details of a single task. Currently, the service layer has the `TaskService.get_task(task_id: UUID) -> TaskModel` method, but there is no CLI entry point to retrieve and display individual task details. Users can only list all tasks, leaving a gap in the CLI interface.

## Problem Statement

Users cannot view the complete details of a single task using the CLI. While the service layer implements task retrieval via `TaskService.get_task(task_id: UUID)`, there is no corresponding CLI command to query and display an individual task. This creates an incomplete user experience where users must list all tasks to find information about a specific task, which is inefficient for large task collections.

## Why

Task retrieval by ID is a fundamental operation in a task management system. Users need to be able to:
- View full details of a specific task by its ID
- See all relevant task metadata: ID, name, details, status, timestamps
- Receive clear error messages for invalid IDs or missing tasks
- Use task IDs discovered from list commands to get more information

Without a show command, the system lacks a basic read operation that complements the create functionality. This change provides critical functionality by exposing the existing service layer through a focused CLI interface.

## What Changes

- Add `tasky task show TASK_ID` CLI command that accepts a task ID as a positional argument
- CLI command calls existing `TaskService.get_task(task_id: UUID)` to retrieve the task
- Command outputs complete task metadata: ID, name, details, status, created timestamp, and updated timestamp
- Add comprehensive input validation with helpful error messages for invalid UUIDs
- Provide clear error messages when a task does not exist
- Integrate with service factory pattern (`create_task_service()`) to respect configured backends
- Add error handling for common failure cases (missing project, storage errors, invalid UUID format)

## Proposed Solution

Add a `tasky task show` CLI command that:
1. Accepts TASK_ID as a positional argument (must be a valid UUID)
2. Calls `TaskService.get_task()` with the provided task ID
3. Returns the retrieved task with all its metadata
4. Provides helpful error messages for invalid UUIDs or missing tasks

### User-Facing Changes

```bash
# View a specific task
tasky task show 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g

# Output example:
# Task Details
# ID: 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g
# Name: Buy groceries
# Details: From the store
# Status: PENDING
# Created: 2025-11-12 14:30:45
# Updated: 2025-11-12 14:30:45
```

### Command Interface

```
tasky task show TASK_ID
  TASK_ID  Task ID (required, UUID format)
```

## Acceptance Criteria

1. CLI command `tasky task show` accepts TASK_ID as a positional argument
2. Command calls `TaskService.get_task()` to retrieve the task
3. Command returns all task details: ID, name, details, status, created timestamp, and updated timestamp
4. TASK_ID argument is required (error shown if missing)
5. TASK_ID must be a valid UUID format (error shown if invalid)
6. Helpful error message displayed if task does not exist
7. Helpful error message displayed for invalid UUID format
8. Command integration with service factory pattern
9. Output is human-readable and well-formatted
10. Test coverage for success and error paths

## Non-Goals

- Task editing from show command output (future enhancement)
- Batch task retrieval (use `task list` with filters)
- JSON output format (stick to human-readable)
- Interactive task modification from show command (future enhancement)

## Dependencies

This change depends on:
- `task-cli-operations` spec (command integration)
- `tasky-tasks` service layer (for `TaskService.get_task()`)
- `tasky-cli` presentation layer (command implementation)

## Risks and Mitigations

**Risk**: Invalid UUID format not validated properly
**Mitigation**: Use Python's `uuid.UUID()` to validate format; Typer can also help with validation decorators

**Risk**: Task not found errors not clearly communicated
**Mitigation**: Follow existing CLI error handling patterns from other commands; test with non-existent IDs

**Risk**: Timestamp format inconsistent with other commands
**Mitigation**: Reuse timestamp formatting utilities from existing commands (e.g., `task list`)

## Impact

- **Affected Specs**:
  - `task-cli-operations`: Adds new CLI command requirement for task retrieval
- **Affected Code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py`: Add `show_command()` function
  - `packages/tasky-cli/src/tasky_cli/commands/__init__.py`: Register command in task group
  - `packages/tasky-cli/tests/test_task_show.py`: Add comprehensive test suite
- **Breaking Changes**: None - purely additive feature

## Alternatives Considered

1. **Add show functionality to list command**: Rejected; list shows all tasks, show is single-task query
2. **Use interactive selection from list**: Rejected as non-standard; CLI tools typically use direct ID reference
3. **Optional output formats (JSON, CSV)**: Rejected to keep scope focused; human-readable first

## Implementation Notes

- Reuse existing service creation patterns from other commands
- Follow output formatting conventions from `task list` command
- Use typer for CLI framework (existing pattern)
- Leverage service factory for dependency injection
- Validate UUID format at CLI layer before calling service
- Handle `TaskNotFound` exception from service layer gracefully

## Related Capabilities

- `task-cli-operations`: Core CLI operations for task commands
- `task-timestamp-management`: Timestamp display and formatting
- `service-factory`: Service instantiation pattern
- `task-domain-exceptions`: Error handling patterns
