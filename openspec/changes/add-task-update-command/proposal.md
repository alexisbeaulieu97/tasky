# Proposal: Add Task Update Command

**Change ID**: `add-task-update-command`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal introduces the `tasky task update` CLI command to enable users to update task metadata (name and/or details) after creation. Currently, the service layer has the `TaskService.update_task()` method, but there is no CLI entry point to use it. This is critical for fixing typos and updating task descriptions.

## Problem Statement

Users cannot update tasks after creation. The service layer already implements task updates (`TaskService.update_task(task: TaskModel) -> None`), but without a corresponding CLI command, users are unable to fix typos or update descriptions. This severely limits the usability of the system for real-world workflows where task details frequently need revision.

## Why

Task management systems must support updates as a core operation. Users need to be able to:
- Fix typos in task names and descriptions
- Update task details as requirements change
- Keep task metadata accurate and relevant
- Retrieve a task, modify only specific fields, and persist those changes

Without an update command, users are forced to delete and recreate tasks, which is inefficient and error-prone. This change provides essential functionality by exposing the existing service layer through the CLI interface.

## What Changes

- Add `tasky task update TASK_ID` CLI command that accepts a task ID as a positional argument
- CLI command accepts optional `--name` and `--details` flags to specify which fields to update
- Require at least one of `--name` or `--details` to be provided
- Command calls `TaskService.get_task()` to retrieve the current task, modifies specified fields, then calls `TaskService.update_task()` to persist changes
- Only specified fields are updated; unspecified fields remain unchanged
- Command outputs the updated task metadata: ID, name, details, status, and last modified timestamp
- Add comprehensive input validation with helpful error messages
- Integrate with service factory pattern (`create_task_service()`) to respect configured backends
- Add error handling for common failure cases (missing task ID, task not found, no fields to update)

## Proposed Solution

Add a `tasky task update` CLI command that:
1. Accepts TASK_ID as a positional argument
2. Accepts `--name` and/or `--details` as optional flags
3. Requires at least one of `--name` or `--details` to be provided
4. Calls `TaskService.get_task(task_id)` to retrieve the task
5. Modifies only the specified fields (name and/or details)
6. Calls `TaskService.update_task(modified_task)` to persist changes
7. Returns the updated task with all metadata
8. Provides helpful error messages for missing or invalid arguments

### User-Facing Changes

```bash
# Update task name only
tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g --name "Updated task name"

# Update task details only
tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g --details "Updated task details"

# Update both name and details
tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g --name "New name" --details "New details"

# Output example:
# Task updated successfully!
# ID: 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g
# Name: Updated task name
# Details: Updated task details
# Status: PENDING
# Modified: 2025-11-12 15:45:30
```

### Command Interface

```
tasky task update TASK_ID [--name NAME] [--details DETAILS]
  TASK_ID    Task ID to update (required, string)
  --name     New task name (optional, string)
  --details  New task details (optional, string)
```

## Acceptance Criteria

1. CLI command `tasky task update` accepts TASK_ID as a positional argument
2. Command accepts `--name` and/or `--details` as optional flags
3. At least one of `--name` or `--details` must be provided (error if neither is given)
4. Command calls `TaskService.get_task(task_id)` to retrieve the task
5. Command modifies only the specified fields in the retrieved task
6. Command calls `TaskService.update_task(modified_task)` to persist changes
7. Unspecified fields remain unchanged in the persisted task
8. Command returns updated task details: ID, name, details, status, and modification timestamp
9. Helpful error messages for missing arguments
10. Helpful error message if task ID is not found
11. Helpful error message if neither `--name` nor `--details` is provided
12. Command integration with service factory pattern
13. Test coverage for all success and error paths

## Non-Goals

- Bulk task updates (future enhancement)
- Update other task fields (status, priority, etc. - future enhancements)
- Task update from file input (future enhancement)
- Conditional updates based on current values (future enhancement)

## Dependencies

This change depends on:
- `task-cli-operations` spec (command integration)
- `tasky-tasks` service layer (for `TaskService.get_task()` and `TaskService.update_task()`)
- `tasky-cli` presentation layer (command implementation)

## Risks and Mitigations

**Risk**: Task not found errors not handled clearly
**Mitigation**: Follow existing CLI error handling patterns and include task ID in error message

**Risk**: Partial updates causing data loss
**Mitigation**: Read full task before modifying, update only specified fields, then persist entire object

**Risk**: Concurrent modifications not handled
**Mitigation**: Not addressed in this change; existing service layer behavior is preserved

**Risk**: User confusion about which fields were updated
**Mitigation**: Display full updated task to confirm all changes

## Impact

- **Affected Specs**:
  - `task-cli-operations`: Adds new CLI command requirement for task updates
- **Affected Code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py`: Add `update_command()` function
  - `packages/tasky-cli/src/tasky_cli/commands/__init__.py`: Register command in task group
  - `packages/tasky-cli/tests/test_task_update.py`: Add comprehensive test suite
- **Breaking Changes**: None - purely additive feature

## Alternatives Considered

1. **Only allow updating one field at a time**: Rejected as less efficient; allowing both fields is intuitive
2. **Use interactive prompts for field selection**: Rejected as non-standard; flags match common CLI conventions
3. **Require all fields in update**: Rejected as inflexible; partial updates are the main use case
4. **Add separate commands for name and details**: Rejected as unnecessarily verbose

## Implementation Notes

- Reuse existing service creation patterns from other commands
- Follow output formatting conventions from `task list` command
- Use typer for CLI framework (existing pattern)
- Leverage service factory for dependency injection
- Validate at least one field is provided at CLI layer before calling service
- Retrieve full task before modification to ensure consistency
- Match error handling patterns from `task list` command

## Related Capabilities

- `task-cli-operations`: Core CLI operations for task commands
- `task-timestamp-management`: Automatic timestamp assignment
- `service-factory`: Service instantiation pattern
