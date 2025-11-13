# Proposal: Add Task Create Command

**Change ID**: `add-task-create-command`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal introduces the `tasky task create` CLI command to enable users to create new tasks from the command line. Currently, the service layer has the `TaskService.create_task()` method, but there is no CLI entry point to use it. This is blocking real usage of the application.

## Problem Statement

Users cannot create tasks using the CLI. The service layer already implements task creation (`TaskService.create_task(name: str, details: str) -> TaskModel`), but without a corresponding CLI command, users cannot interact with this functionality. This blocks real-world usage until the basic create command is implemented.

## Why

Task creation is the most fundamental operation in a task management system. Users need to be able to:
- Create new tasks quickly from the command line
- Immediately see the created task with its ID for reference
- Receive clear error messages if the operation fails

Without a create command, the system is incomplete and unsuitable for actual use. This change provides immediate, unblocking value by exposing the existing service layer through the CLI interface.

## What Changes

- Add `tasky task create NAME DETAILS` CLI command that accepts task name and details as positional arguments
- CLI command calls existing `TaskService.create_task(name, details)` to create and persist the task
- Command outputs created task metadata: ID, name, details, status (always PENDING), and creation timestamp
- Add comprehensive input validation with helpful error messages for missing arguments
- Integrate with service factory pattern (`create_task_service()`) to respect configured backends
- Add error handling for common failure cases (missing project, storage errors, permission issues)

## Proposed Solution

Add a `tasky task create` CLI command that:
1. Accepts NAME and DETAILS as positional arguments
2. Calls `TaskService.create_task()` with the provided arguments
3. Returns the created task with its ID, name, creation timestamp, and status
4. Provides helpful error messages for missing or invalid arguments

### User-Facing Changes

```bash
# Create a new task
tasky task create "Buy groceries" "From the store"

# Output example:
# Task created successfully!
# ID: 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g
# Name: Buy groceries
# Details: From the store
# Status: PENDING
# Created: 2025-11-12 14:30:45
```

### Command Interface

```
tasky task create NAME DETAILS
  NAME     Task name (required, string)
  DETAILS  Task details/description (required, string)
```

## Acceptance Criteria

1. CLI command `tasky task create` accepts NAME and DETAILS as positional arguments
2. Command calls `TaskService.create_task()` to create the task
3. Command returns created task details: ID, name, details, status, and creation timestamp
4. NAME argument is required (error shown if missing)
5. DETAILS argument is required (error shown if missing)
6. Status is always PENDING for newly created tasks
7. Creation timestamp is automatically set by the service
8. Helpful error messages for missing arguments
9. Command integration with service factory pattern
10. Test coverage for success and error paths

## Non-Goals

- Task editing from CLI (future enhancement)
- Bulk task creation (future enhancement)
- Task creation from file input (future enhancement)
- Advanced validation of name/details format (use reasonable defaults)

## Dependencies

This change depends on:
- `task-cli-operations` spec (command integration)
- `tasky-tasks` service layer (for `TaskService.create_task()`)
- `tasky-cli` presentation layer (command implementation)

## Risks and Mitigations

**Risk**: Missing error handling for invalid service calls
**Mitigation**: Follow existing CLI error handling patterns from `task list` command

**Risk**: Task creation timestamp not set correctly
**Mitigation**: Service layer already handles timestamp assignment; verify in tests

**Risk**: Created task ID not visible to users
**Mitigation**: Include ID prominently in output for reference in future commands

## Impact

- **Affected Specs**:
  - `task-cli-operations`: Adds new CLI command requirement for task creation
- **Affected Code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py`: Add `create_command()` function
  - `packages/tasky-cli/src/tasky_cli/commands/__init__.py`: Register command in task group
  - `packages/tasky-cli/tests/test_task_create.py`: Add comprehensive test suite
- **Breaking Changes**: None - purely additive feature

## Alternatives Considered

1. **Add only to API first, CLI later**: Rejected as blocking real usage now
2. **Use interactive prompts**: Rejected as non-standard; positional args match common tools
3. **Optional details parameter**: Rejected to keep command simple and consistent

## Implementation Notes

- Reuse existing service creation patterns from other commands
- Follow output formatting conventions from `task list` command
- Use typer for CLI framework (existing pattern)
- Leverage service factory for dependency injection
- Validate required arguments at CLI layer before calling service

## Related Capabilities

- `task-cli-operations`: Core CLI operations for task commands
- `task-timestamp-management`: Automatic timestamp assignment
- `service-factory`: Service instantiation pattern
