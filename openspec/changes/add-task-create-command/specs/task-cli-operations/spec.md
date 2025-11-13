# Spec: Task Create Command

**Capability**: `task-cli-operations`
**Status**: Draft
**Package**: `tasky-cli`
**Layer**: Presentation

## Overview

Extends the task CLI with a `create` command that enables users to create new tasks from the command line. Provides a simple, efficient interface for task creation with clear output and error handling.

---

## ADDED Requirements

### Requirement: Task Create Command with Positional Arguments

The system SHALL provide a CLI command `tasky task create NAME DETAILS` that creates a new task.

**Rationale**: Users need a simple, efficient way to create tasks from the command line. Positional arguments provide a natural, discoverable interface that matches common CLI conventions.

#### Scenario: Create task successfully

**Given** a project is initialized with task storage configured
**When** the user runs `tasky task create "Buy milk" "From the store"`
**Then** the CLI SHALL call `TaskService.create_task("Buy milk", "From the store")`
**And** the created task SHALL be persisted to the configured storage backend
**And** the CLI SHALL display the task ID prominently
**And** the CLI SHALL display the task name, details, status (PENDING), and creation timestamp

#### Scenario: Create task with special characters in name

**Given** a project is initialized
**When** the user runs `tasky task create "Fix bug #123: Handle null pointer" "Check cache initialization logic"`
**Then** the task SHALL be created with the name exactly as provided
**And** special characters (# : & etc) SHALL be preserved
**And** the created task SHALL be retrievable with `tasky task list`

#### Scenario: Create task with multiword details

**Given** a project is initialized
**When** the user runs `tasky task create "Meeting" "Discuss project timeline, budget allocation, and team assignments"`
**Then** the task SHALL be created with all details preserved
**And** line breaks or special formatting SHALL be handled correctly

---

### Requirement: Task Create Command Returns Task Metadata

The system SHALL return created task metadata including ID, name, details, status, and creation timestamp.

**Rationale**: Users need the task ID immediately to reference the task in subsequent operations (filtering, status updates). The creation timestamp confirms when the task was added.

#### Scenario: Output includes unique task ID

**Given** a newly created task
**When** the create command completes
**Then** the output SHALL include a unique task ID
**And** the ID SHALL be in a format suitable for use in future commands
**And** no two created tasks SHALL have the same ID

#### Scenario: Output includes creation timestamp

**Given** a task is created at 2025-11-12 14:30:45
**When** the command displays the created task
**Then** the output SHALL include the creation timestamp
**And** the timestamp format SHALL be human-readable (ISO 8601 or similar)
**And** the timestamp SHALL be accurate to at least second precision

#### Scenario: Output includes initial PENDING status

**Given** a task is newly created
**When** the create command returns task metadata
**Then** the status SHALL always be `PENDING`
**And** no other status value SHALL be assigned during creation
**And** the status SHALL be modifiable by subsequent commands

---

### Requirement: Task Create Command Validates Required Arguments

The system SHALL require both NAME and DETAILS arguments and provide helpful error messages when they are missing.

**Rationale**: Clear error handling prevents confusion and guides users toward correct usage, improving user experience.

#### Scenario: Error when NAME argument missing

**Given** the user runs `tasky task create` without NAME argument
**When** the CLI validates the arguments
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate that NAME is required
**And** the error message SHALL show correct command syntax
**And** the CLI SHALL exit with status code 1 (error)
**And** no task SHALL be created

#### Scenario: Error when DETAILS argument missing

**Given** the user runs `tasky task create "Buy milk"` without DETAILS argument
**When** the CLI validates the arguments
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate that DETAILS is required
**And** the error message SHALL show correct command syntax with both arguments
**And** the CLI SHALL exit with status code 1 (error)

#### Scenario: Display command syntax in help

**Given** the user runs `tasky task create --help`
**When** the help text is displayed
**Then** the help text SHALL describe the NAME and DETAILS arguments
**And** the help text SHALL show example usage: `tasky task create "Task name" "Task details"`
**And** the help text SHALL explain what each argument represents
**And** the help text SHALL indicate both arguments are required

---

### Requirement: Task Create Command Uses Service Factory

The create command SHALL use `create_task_service()` factory function to instantiate the task service.

**Rationale**: Ensures the command respects configured storage backends and settings, maintaining consistency with other task commands.

#### Scenario: Create command respects JSON backend configuration

**Given** a project with config specifying backend "json"
**When** the user runs `tasky task create "Test task" "Test details"`
**Then** the create command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `JsonTaskRepository`
**And** the task SHALL be persisted to the JSON backend
**And** the created task SHALL be retrievable via JSON storage

#### Scenario: Create command respects SQLite backend configuration

**Given** a project with config specifying backend "sqlite"
**And** the "sqlite" backend is registered
**When** the user runs `tasky task create "Test task" "Test details"`
**Then** the create command SHALL call `create_task_service()`
**And** the factory SHALL return a service with `SqliteTaskRepository`
**And** the task SHALL be persisted to the SQLite database
**And** the created task SHALL be retrievable via SQLite storage

---

### Requirement: Task Create Command Handles Service Errors Gracefully

The system SHALL catch and report task creation errors with helpful messages.

**Rationale**: Prevents cryptic error output and helps users understand what went wrong, enabling them to take corrective action.

#### Scenario: Handle storage permission errors

**Given** the storage backend has insufficient permissions to create files
**When** the user runs `tasky task create "Task" "Details"`
**Then** the CLI SHALL catch the permission error
**And** the CLI SHALL display a helpful message
**And** the message SHALL suggest checking file permissions or storage location
**And** the CLI SHALL exit with status code 1

#### Scenario: Handle project not found error

**Given** no project is initialized in the current directory or parent directories
**When** the user runs `tasky task create "Task" "Details"`
**Then** the CLI SHALL display an error message
**And** the error message SHALL indicate "No project found"
**And** the error message SHALL suggest running `tasky project init` first
**And** the CLI SHALL exit with status code 1

---

## Implementation Notes

- **File**: `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
- **Function**: `create_command(name: str, details: str) -> None:`
- **Command Registration**: Add to task subcommand group
- **Service Integration**: Use `create_task_service()` factory function
- **Output Format**: Match existing task list output formatting conventions
- **Error Handling**: Follow patterns established by `list_command()`
- **Dependencies**: Requires `TaskService.create_task()` from `tasky_tasks` package

## Testing Requirements

- Unit tests for command argument validation
- Integration tests with real task service and storage backends
- Error case testing (missing arguments, permission errors, no project)
- Output format verification
- Full end-to-end workflow testing

**Test Files**:
- `packages/tasky-cli/tests/test_task_create.py` - Command tests
- Integration tests in existing test suites

---

## Related Specifications

- `task-cli-operations`: Core CLI operations
- `service-factory`: Service instantiation pattern
- `task-timestamp-management`: Automatic timestamp assignment
- `task-domain-exceptions`: Error handling patterns
