# Spec: Task Update Command

**Capability**: `task-cli-operations`
**Status**: Draft
**Package**: `tasky-cli`
**Layer**: Presentation

## Overview

Extends the task CLI with an `update` command that enables users to update task metadata (name and/or details) after creation. Provides a flexible, efficient interface for task updates with clear output and error handling.

---

## ADDED Requirements

### Requirement: Task Update Command with Positional ID and Optional Field Flags

The system SHALL provide a CLI command `tasky task update TASK_ID [--name NAME] [--details DETAILS]` that updates an existing task's metadata.

**Rationale**: Users need an efficient way to fix typos and update task descriptions after creation. Optional field flags allow flexible, partial updates without requiring users to re-enter unchanged data.

#### Scenario: Update task name only

**Given** a task with ID `3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`, name "Buy milk", and details "From the store"
**When** the user runs `tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g --name "Buy organic milk"`
**Then** the CLI SHALL call `TaskService.get_task(task_id)`
**And** the CLI SHALL modify only the name field in the retrieved task
**And** the CLI SHALL call `TaskService.update_task(modified_task)` to persist changes
**And** the task name SHALL change to "Buy organic milk"
**And** the task details SHALL remain "From the store" (unchanged)
**And** the CLI SHALL display the updated task with all metadata

#### Scenario: Update task details only

**Given** a task with ID `abc123`, name "Meeting", and details "Thursday 2pm"
**When** the user runs `tasky task update abc123 --details "Thursday 2pm in Conference Room B"`
**Then** the CLI SHALL call `TaskService.get_task(task_id)`
**And** the CLI SHALL modify only the details field in the retrieved task
**And** the CLI SHALL call `TaskService.update_task(modified_task)`
**And** the task name SHALL remain "Meeting" (unchanged)
**And** the task details SHALL change to "Thursday 2pm in Conference Room B"
**And** the CLI SHALL display the updated task confirming changes

#### Scenario: Update both name and details

**Given** a task with ID `xyz789`, name "Fix bug", details "Cache issue"
**When** the user runs `tasky task update xyz789 --name "Fix cache invalidation bug" --details "Address race condition in cache initialization"`
**Then** the CLI SHALL call `TaskService.get_task(task_id)`
**And** the CLI SHALL modify both name and details fields in the retrieved task
**And** the CLI SHALL call `TaskService.update_task(modified_task)`
**And** the task name SHALL change to "Fix cache invalidation bug"
**And** the task details SHALL change to "Address race condition in cache initialization"
**And** the CLI SHALL display the updated task with both changes confirmed

#### Scenario: Update with special characters in name

**Given** a task with ID `special123`
**When** the user runs `tasky task update special123 --name "Fix bug #456: Handle null & undefined"`
**Then** the task name SHALL change to exactly "Fix bug #456: Handle null & undefined"
**And** special characters (# : & etc) SHALL be preserved
**And** the updated task SHALL be retrievable with `tasky task list`

#### Scenario: Update with multiword details

**Given** a task with ID `words123`
**When** the user runs `tasky task update words123 --details "Discuss timeline, allocate budget, assign team members, review scope"`
**Then** the task details SHALL be updated with all text preserved
**And** multiword and multi-clause details SHALL be handled correctly

---

### Requirement: Task Update Command Validates Required Arguments

The system SHALL require TASK_ID as a positional argument and at least one of `--name` or `--details` flags. It SHALL provide helpful error messages when arguments are missing or invalid.

**Rationale**: Clear validation prevents user confusion and ensures the command has meaningful work to perform, improving user experience.

#### Scenario: Error when TASK_ID argument missing

**Given** the user runs `tasky task update` without TASK_ID argument
**When** the CLI validates the arguments
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate that TASK_ID is required
**And** the error message SHALL show correct command syntax
**And** the CLI SHALL exit with status code 1 (error)
**And** no task SHALL be updated

#### Scenario: Error when neither --name nor --details provided

**Given** the user runs `tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g` without any field flags
**When** the CLI validates the arguments
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate that at least one of `--name` or `--details` is required
**And** the error message SHALL show example usage with field flags
**And** the CLI SHALL exit with status code 1 (error)
**And** no task SHALL be updated

#### Scenario: Task ID does not exist

**Given** a task ID `nonexistent-id` that does not exist in the project
**When** the user runs `tasky task update nonexistent-id --name "Updated"`
**Then** the CLI SHALL call `TaskService.get_task(nonexistent-id)`
**And** the service SHALL raise an exception (task not found)
**And** the CLI SHALL display an error message
**And** the error message SHALL indicate the task with that ID was not found
**And** the error message MAY suggest listing tasks with `tasky task list`
**And** the CLI SHALL exit with status code 1

#### Scenario: Display command syntax in help

**Given** the user runs `tasky task update --help`
**When** the help text is displayed
**Then** the help text SHALL describe the TASK_ID positional argument
**And** the help text SHALL describe the `--name` optional flag
**And** the help text SHALL describe the `--details` optional flag
**And** the help text SHALL show example usage: `tasky task update <task-id> --name "New name" --details "New details"`
**And** the help text SHALL indicate that TASK_ID is required
**And** the help text SHALL indicate that at least one field flag is required
**And** the help text SHALL show examples of updating individual fields

---

### Requirement: Task Update Command Returns Updated Task Metadata

The system SHALL return updated task metadata including ID, name, details, status, and modification timestamp.

**Rationale**: Users need immediate confirmation that the update succeeded and can see the exact state of the updated task, including any auto-assigned timestamps.

#### Scenario: Output includes unique task ID

**Given** an updated task
**When** the update command completes
**Then** the output SHALL include the task ID
**And** the ID displayed SHALL match the ID provided in the command
**And** the ID format SHALL be suitable for use in future commands

#### Scenario: Output includes updated name and details

**Given** a task was successfully updated with new name and/or details
**When** the command displays the updated task
**Then** the output SHALL include the new task name
**And** the output SHALL include the new task details
**And** the displayed values SHALL match exactly what was provided in the `--name` and `--details` flags

#### Scenario: Output includes status and timestamp

**Given** a task is updated at 2025-11-12 15:45:30
**When** the command displays the updated task
**Then** the output SHALL include the task status
**And** the status SHALL match the task's current status (unchanged by update unless status field is later supported)
**And** the output MAY include the update/modification timestamp
**And** any timestamp SHALL be human-readable (ISO 8601 or similar)

---

### Requirement: Task Update Command Uses Service Factory

The update command SHALL use `create_task_service()` factory function to instantiate the task service.

**Rationale**: Ensures the command respects configured storage backends and settings, maintaining consistency with other task commands.

#### Scenario: Update command respects JSON backend configuration

**Given** a project with config specifying backend "json"
**And** a task exists in the JSON backend
**When** the user runs `tasky task update <task-id> --name "Updated"`
**Then** the update command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `JsonTaskRepository`
**And** the updated task SHALL be persisted to the JSON backend
**And** the task retrieved via JSON storage SHALL reflect the updates

#### Scenario: Update command respects SQLite backend configuration

**Given** a project with config specifying backend "sqlite"
**And** the "sqlite" backend is registered
**And** a task exists in the SQLite database
**When** the user runs `tasky task update <task-id> --details "Updated details"`
**Then** the update command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `SqliteTaskRepository`
**And** the updated task SHALL be persisted to the SQLite database
**And** the task retrieved via SQLite storage SHALL reflect the updates

---

### Requirement: Task Update Command Handles Service Errors Gracefully

The system SHALL catch and report task update errors with helpful messages.

**Rationale**: Prevents cryptic error output and helps users understand what went wrong, enabling them to take corrective action.

#### Scenario: Handle storage permission errors

**Given** the storage backend has insufficient permissions to update files
**When** the user runs `tasky task update <task-id> --name "Updated"`
**Then** the CLI SHALL catch the permission error
**And** the CLI SHALL display a helpful message
**And** the message SHALL suggest checking file permissions or storage location
**And** the CLI SHALL exit with status code 1
**And** the original task SHALL remain unchanged

#### Scenario: Handle project not found error

**Given** no project is initialized in the current directory or parent directories
**When** the user runs `tasky task update <task-id> --name "Updated"`
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate "No project found"
**And** the error message SHALL suggest running `tasky project init` first
**And** the CLI SHALL exit with status code 1

#### Scenario: Handle service layer exceptions

**Given** the task service raises an exception during update
**When** the user runs `tasky task update <task-id> --name "Updated"`
**Then** the CLI SHALL catch the service exception
**And** the CLI SHALL display a user-friendly error message
**And** the message SHALL not expose internal stack traces or implementation details
**And** the CLI SHALL exit with status code 1

---

### Requirement: Task Update Command Preserves Unmodified Fields

The system SHALL ensure that fields not specified in the update command remain unchanged in the persisted task.

**Rationale**: Partial updates are the primary use case; users should not need to re-enter unchanged data, and unintended field modifications must be prevented.

#### Scenario: Unmodified name preserved when updating details

**Given** a task with ID `preserve123`, name "Original name", status "PENDING", and details "Original details"
**When** the user runs `tasky task update preserve123 --details "New details"`
**Then** the task name SHALL remain "Original name"
**And** the task status SHALL remain "PENDING"
**And** only the details field SHALL change
**And** when the task is retrieved again, all non-modified fields SHALL be identical to the original

#### Scenario: Unmodified details preserved when updating name

**Given** a task with ID `preserve456`, name "Old name", status "PENDING", and details "Important details"
**When** the user runs `tasky task update preserve456 --name "New name"`
**Then** the task details SHALL remain "Important details"
**And** the task status SHALL remain "PENDING"
**And** only the name field SHALL change
**And** when the task is retrieved again, all non-modified fields SHALL be identical to the original

#### Scenario: All non-specified fields preserved when updating both name and details

**Given** a task with ID `preserve789`, name "Current name", status "PENDING", details "Current details", and creation timestamp "2025-11-11 10:00:00"
**When** the user runs `tasky task update preserve789 --name "New name" --details "New details"`
**Then** the task status SHALL remain "PENDING"
**And** the creation timestamp SHALL remain "2025-11-11 10:00:00"
**And** only name and details fields SHALL change
**And** when the task is retrieved again, all non-modified fields SHALL be identical to the original

---

## Implementation Notes

- **File**: `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
- **Function**: `update_command(task_id: str, name: Optional[str] = None, details: Optional[str] = None) -> None:`
- **Command Registration**: Add to task subcommand group
- **Service Integration**: Use `create_task_service()` factory function
- **Retrieval Pattern**: Call `get_task()` before modification to ensure consistency
- **Field Modification**: Modify only non-None fields in retrieved task
- **Persistence Pattern**: Call `update_task()` with complete modified task object
- **Output Format**: Match existing task list output formatting conventions
- **Error Handling**: Follow patterns established by `list_command()` and `create_command()`
- **Validation**: Check at CLI layer that at least one field flag is provided before service call
- **Dependencies**: Requires `TaskService.get_task()` and `TaskService.update_task()` from `tasky_tasks` package

## Testing Requirements

- Unit tests for command argument validation
- Unit tests for field flag validation (at least one required)
- Integration tests with real task service and storage backends
- Error case testing (missing arguments, task not found, permission errors, no project)
- Field isolation testing (verify unmodified fields remain unchanged)
- Output format verification
- Full end-to-end workflow testing
- Multi-scenario testing (name only, details only, both fields)

**Test Files**:
- `packages/tasky-cli/tests/test_task_update.py` - Command tests
- Integration tests in existing test suites

---

## Related Specifications

- `task-cli-operations`: Core CLI operations
- `service-factory`: Service instantiation pattern
- `task-timestamp-management`: Timestamp assignment and handling
- `task-domain-exceptions`: Error handling patterns
