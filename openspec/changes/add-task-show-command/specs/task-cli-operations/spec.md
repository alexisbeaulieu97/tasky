# Spec: Task Show Command

**Capability**: `task-cli-operations`
**Status**: Draft
**Package**: `tasky-cli`
**Layer**: Presentation

## Overview

Extends the task CLI with a `show` command that enables users to view the complete details of a single task by its ID. Provides a focused interface for task retrieval with clear output and comprehensive error handling for invalid IDs and missing tasks.

---

## ADDED Requirements

### Requirement: Task Show Command with UUID Argument

The system SHALL provide a CLI command `tasky task show TASK_ID` that retrieves and displays a single task.

**Rationale**: Users need an efficient way to view the full details of a specific task by its ID. This complements the list command and provides direct task access.

#### Scenario: Show valid task successfully

**Given** a project is initialized with task storage configured
**And** a task with ID `3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g` exists in storage
**When** the user runs `tasky task show 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`
**Then** the CLI SHALL call `TaskService.get_task()` with the provided UUID
**And** the task SHALL be retrieved from the configured storage backend
**And** all task metadata SHALL be displayed to the user

#### Scenario: Show task with special characters in details

**Given** a project is initialized
**And** a task exists with name containing special characters: "Fix bug #123: Handle null pointer"
**And** a task exists with details containing special characters: "Check cache & memory allocation (critical!)"
**When** the user runs `tasky task show <task-id>`
**Then** all special characters in the task name and details SHALL be preserved and displayed correctly
**And** the output SHALL be properly formatted despite special characters

#### Scenario: Show task after modification

**Given** a task was created at 2025-11-12 14:00:00
**And** the task status was updated to COMPLETED at 2025-11-12 15:00:00
**When** the user runs `tasky task show <task-id>`
**Then** the created timestamp SHALL show 2025-11-12 14:00:00
**And** the updated timestamp SHALL show 2025-11-12 15:00:00
**And** the current status (COMPLETED) SHALL be displayed

---

### Requirement: Task Show Command Returns Complete Task Metadata

The system SHALL display all task details: ID, name, details, status, created timestamp, and updated timestamp.

**Rationale**: Users need comprehensive task information for reference and verification. Complete metadata enables informed decision-making about task actions.

#### Scenario: Output includes task ID

**Given** a task with unique ID `3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`
**When** the show command displays the task
**Then** the output SHALL include the task ID prominently
**And** the ID format SHALL be in UUID format (e.g., `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
**And** the ID SHALL be easily copyable for use in other commands

#### Scenario: Output includes task name and details

**Given** a task with name "Buy groceries" and details "From the store"
**When** the show command displays the task
**Then** the output SHALL include "Buy groceries" as the task name
**And** the output SHALL include "From the store" as the task details
**And** both fields SHALL be clearly labeled

#### Scenario: Output includes timestamps with precision

**Given** a task created at 2025-11-12 14:30:45.123456
**When** the show command displays the task
**Then** the created timestamp SHALL be displayed in human-readable format
**And** the timestamp format SHALL be ISO 8601 or equivalent (e.g., `2025-11-12 14:30:45`)
**And** the precision SHALL be to at least second level (HH:MM:SS)
**And** the updated timestamp SHALL also be displayed if different from created time

#### Scenario: Output includes current task status

**Given** a task with current status PENDING
**When** the show command displays the task
**Then** the status SHALL be displayed prominently
**And** the status value SHALL match the actual stored status in the backend
**And** if status changes, the shown status SHALL reflect the latest value

---

### Requirement: Task Show Command Validates UUID Format

The system SHALL validate the TASK_ID argument as a valid UUID and provide helpful error messages for invalid formats.

**Rationale**: UUID validation prevents confusing errors and guides users toward correct usage.

#### Scenario: Error for invalid UUID format

**Given** the user runs `tasky task show not-a-uuid`
**When** the CLI validates the UUID format
**Then** the CLI SHALL detect that "not-a-uuid" is not a valid UUID
**And** the CLI SHALL display an error message
**And** the error message SHALL indicate "Invalid UUID format"
**And** the error message SHALL show the expected UUID format
**And** the CLI SHALL exit with status code 1 (error)
**And** no service call SHALL be made

#### Scenario: Error for malformed UUID

**Given** the user runs `tasky task show 3af4b92f-invalid`
**When** the CLI validates the UUID
**Then** the CLI SHALL reject the malformed UUID
**And** the error message SHALL indicate the UUID is invalid
**And** the CLI SHALL exit with error status
**And** no query SHALL be executed against storage

#### Scenario: Accept valid UUID variants

**Given** the user provides a valid UUID in standard format: `3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`
**When** the CLI validates the UUID
**Then** the UUID SHALL be accepted as valid
**And** the service call SHALL proceed normally
**And** the task SHALL be retrieved if it exists

---

### Requirement: Task Show Command Handles Missing Tasks

The system SHALL provide clear error messages when the specified task does not exist.

**Rationale**: Clear error communication helps users understand why a task cannot be retrieved and what to do next.

#### Scenario: Error when task does not exist

**Given** the user runs `tasky task show 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`
**And** no task with that ID exists in storage
**When** the CLI calls `TaskService.get_task()`
**Then** the service SHALL raise an exception (e.g., `TaskNotFound`)
**And** the CLI SHALL catch this exception
**And** the CLI SHALL display an error message
**And** the error message SHALL indicate "Task not found"
**And** the error message SHALL include the task ID that was not found
**And** the CLI SHALL suggest using `tasky task list` to see available tasks
**And** the CLI SHALL exit with status code 1

#### Scenario: Distinguish between "task not found" and "invalid UUID"

**Given** two error scenarios: (1) valid UUID but missing task, (2) invalid UUID format
**When** both produce errors
**Then** the error messages SHALL be distinct
**And** invalid UUID errors SHALL mention format/syntax issues
**And** missing task errors SHALL mention that the task could not be found
**And** users SHALL be able to understand the difference

---

### Requirement: Task Show Command Uses Service Factory

The show command SHALL use `create_task_service()` factory function to instantiate the task service.

**Rationale**: Ensures the command respects configured storage backends and settings, maintaining consistency with other task commands.

#### Scenario: Show command respects JSON backend configuration

**Given** a project with config specifying backend "json"
**When** the user runs `tasky task show <task-id>`
**Then** the show command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `JsonTaskRepository`
**And** the task SHALL be retrieved from the JSON backend
**And** the task data SHALL reflect the JSON storage state

#### Scenario: Show command respects SQLite backend configuration

**Given** a project with config specifying backend "sqlite"
**And** the "sqlite" backend is registered
**When** the user runs `tasky task show <task-id>`
**Then** the show command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `SqliteTaskRepository`
**And** the task SHALL be retrieved from the SQLite database
**And** the task data SHALL reflect the database state

---

### Requirement: Task Show Command Handles Service Errors Gracefully

The system SHALL catch and report task retrieval errors with helpful messages.

**Rationale**: Prevents cryptic error output and helps users understand what went wrong, enabling them to take corrective action.

#### Scenario: Handle storage permission errors

**Given** the storage backend has insufficient permissions to read files
**When** the user runs `tasky task show <task-id>`
**Then** the CLI SHALL catch the permission error
**And** the CLI SHALL display a helpful message
**And** the message SHALL suggest checking file permissions or storage location
**And** the CLI SHALL exit with status code 1

#### Scenario: Handle project not found error

**Given** no project is initialized in the current directory or parent directories
**When** the user runs `tasky task show <task-id>`
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate "No project found"
**And** the error message SHALL suggest running `tasky project init` first
**And** the CLI SHALL exit with status code 1

#### Scenario: Handle storage connection errors

**Given** the storage backend (e.g., database) is unavailable or corrupted
**When** the user runs `tasky task show <task-id>`
**Then** the CLI SHALL catch the storage error
**And** the CLI SHALL display a meaningful error message
**And** the message SHALL NOT expose internal implementation details
**And** the CLI SHALL exit with status code 1

---

### Requirement: Task Show Command Has Clear Help Text

The system SHALL provide clear help documentation for the show command.

**Rationale**: Users need to understand how to use the command and what arguments are required.

#### Scenario: Help text describes the command

**Given** the user runs `tasky task show --help`
**When** the help text is displayed
**Then** the help text SHALL describe what the command does
**And** the description SHALL explain that it retrieves a single task by ID
**And** the help text SHALL show the command syntax: `tasky task show TASK_ID`

#### Scenario: Help text describes TASK_ID parameter

**Given** the user runs `tasky task show --help`
**When** the help text is displayed
**Then** the help text SHALL describe the TASK_ID parameter
**And** it SHALL indicate that TASK_ID is a UUID format
**And** it SHALL indicate that TASK_ID is required
**And** it SHALL include an example UUID

#### Scenario: Help text includes usage example

**Given** the user runs `tasky task show --help`
**When** the help text is displayed
**Then** the help text SHALL include a usage example
**And** the example SHALL show: `tasky task show 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f6g`
**And** the example SHALL demonstrate proper UUID format
**And** the example SHALL be realistic and easy to understand

---

## Implementation Notes

- **File**: `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
- **Function**: `show_command(task_id: str) -> None:`
- **Command Registration**: Add to task subcommand group
- **Service Integration**: Use `create_task_service()` factory function
- **UUID Validation**: Use Python `uuid.UUID()` to parse and validate TASK_ID
- **Output Format**: Match existing task list output formatting conventions
- **Error Handling**: Follow patterns established by `list_command()`
- **Dependencies**: Requires `TaskService.get_task()` from `tasky_tasks` package

## Testing Requirements

- Unit tests for command argument validation
- Unit tests for UUID format validation and error handling
- Integration tests with real task service and storage backends
- Error case testing (missing arguments, invalid UUID, non-existent task, no project, permission errors)
- Output format verification
- Full end-to-end workflow testing (create task, show task, verify output)

**Test Files**:
- `packages/tasky-cli/tests/test_task_show.py` - Command tests
- Integration tests in existing test suites

---

## Related Specifications

- `task-cli-operations`: Core CLI operations
- `service-factory`: Service instantiation pattern
- `task-timestamp-management`: Timestamp display and formatting
- `task-domain-exceptions`: Error handling patterns
