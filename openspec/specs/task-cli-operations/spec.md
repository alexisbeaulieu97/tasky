# task-cli-operations Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
### Requirement: Task commands use service factory

All task CLI commands SHALL use `create_task_service()` instead of directly instantiating repositories.

#### Scenario: List tasks using factory

```gherkin
Given a project with config specifying backend "json"
And the project contains 2 tasks
When I run "tasky task list"
Then the command calls create_task_service()
And the service uses the configured backend
And both tasks are displayed
```

#### Scenario: Create task using factory

```gherkin
Given a project with config specifying backend "json"
When I run 'tasky task create "Buy milk" "From the store"'
Then the command calls create_task_service()
And a new task is created via the configured backend
And the CLI outputs "Task created: Buy milk"
```

---

### Requirement: Error handling for missing project

Task commands SHALL provide helpful error messages when no project is initialized.

#### Scenario: List tasks without project initialization

```gherkin
Given no ".tasky/config.json" exists in current directory or parents
When I run "tasky task list"
Then it exits with error code 1
And the error message includes "No project found"
And the error message includes "Run 'tasky project init' first"
```

#### Scenario: Create task without project initialization

```gherkin
Given no project is initialized
When I run 'tasky task create "Task" "Details"'
Then it exits with error code 1
And the error message suggests running "tasky project init"
```

---

### Requirement: Transparent backend selection

Task commands SHALL work with any registered backend without code changes.

#### Scenario: List tasks with SQLite backend

```gherkin
Given a project with config specifying backend "sqlite"
And the "sqlite" backend is registered
When I run "tasky task list"
Then the command uses SqliteTaskRepository
And tasks are retrieved from the SQLite database
And tasks are displayed correctly
```

#### Scenario: List tasks with JSON backend

```gherkin
Given a project with config specifying backend "json"
When I run "tasky task list"
Then the command uses JsonTaskRepository
And tasks are retrieved from the JSON file
```

---

### Requirement: Backend configuration errors

Task commands SHALL handle backend configuration errors gracefully.

#### Scenario: Configured backend not registered

```gherkin
Given a config file specifying backend "postgres"
But no "postgres" backend is registered
When I run "tasky task list"
Then it exits with error code 1
And the error message includes "Backend 'postgres' not found"
And the error message lists available backends
```

---

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
**And** special characters (# : & etc.) SHALL be preserved
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

### Requirement: Task List Command Maintains Consistent Output Format

The `task list` command output format MUST remain consistent whether displaying filtered or unfiltered tasks, and MUST support AND-logic combination of multiple filter criteria.

**Original Behavior**: List command displays all tasks or filtered-by-status tasks with basic formatting.

**Modified Behavior**: List command displays filtered tasks (by status, date, or search) while maintaining consistent formatting and supporting AND-logic combination of criteria.

**Rationale**: Users expect consistent output formatting regardless of which filters are applied, and multiple independent filters must work together predictably using AND logic (all criteria must match).

#### Scenario: Filtered output matches existing format

**WHEN** the user applies any combination of filters
**THEN** the output format SHALL remain identical to the status-only filtering format
**AND** each task SHALL display the same fields in the same order
**AND** no additional metadata SHALL be added without explicit design

#### Scenario: Backward compatibility maintained

**WHEN** users run existing commands without new filter options
**THEN** behavior SHALL be identical to current implementation
**AND** `tasky task list --status pending` SHALL work unchanged
**AND** `tasky task list` with no filters SHALL show all tasks unchanged

#### Scenario: Multiple filters combine using AND logic

**WHEN** the user applies multiple filter options
**THEN** the system SHALL require all filter criteria to match (AND logic)
**AND** tasks that satisfy only some criteria SHALL NOT be displayed
**AND** only tasks matching every specified criterion SHALL appear

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

### Requirement: Task Listing Output Format

The `task list` command SHALL display tasks with status indicators, task IDs, and optional timestamps to provide users with essential task management information.

**Rationale**: Users need to see task status and IDs to effectively manage tasks and reference them in other commands. The enhanced output format provides critical context without requiring additional commands.

#### Scenario: List tasks displays status indicators and IDs

**Given** a project with 3 tasks in various statuses:
- Task 1: name="Buy milk", details="From the store", status=PENDING
- Task 2: name="Review PR", details="Code review", status=COMPLETED
- Task 3: name="Old project", details="Archived", status=CANCELLED

**When** the user runs `tasky task list`

**Then** the output SHALL display each task with format:
```
○ {task.id} {task.name} - {task.details}
✓ {task.id} {task.name} - {task.details}
✗ {task.id} {task.name} - {task.details}
```

**And** the status symbol SHALL map to task status:
- ○ (PENDING) for tasks with status = PENDING
- ✓ (COMPLETED) for tasks with status = COMPLETED
- ✗ (CANCELLED) for tasks with status = CANCELLED

**And** the task ID SHALL be displayed in UUID format (36 characters with hyphens)

**And** the output SHALL NOT include any additional formatting or colors beyond the required symbols

#### Scenario: List tasks are sorted by status

**Given** a project with tasks in mixed statuses (CANCELLED, PENDING, COMPLETED)

**When** the user runs `tasky task list`

**Then** the output SHALL display tasks in this order:
1. All PENDING tasks first
2. All COMPLETED tasks second
3. All CANCELLED tasks last

**And** within each status group, tasks SHALL appear in consistent order (preserving creation order or ID sort)

**And** the sorting SHALL apply regardless of the original insertion order

#### Scenario: List displays summary count

**Given** a project with:
- 5 PENDING tasks
- 3 COMPLETED tasks
- 2 CANCELLED tasks

**When** the user runs `tasky task list`

**Then** the output SHALL include a summary line after all tasks:
```
Showing 10 tasks (5 pending, 3 completed, 2 cancelled)
```

**And** the summary line SHALL use proper singular/plural forms:
- "1 task" if total is 1
- "X tasks" if total is not 1

**And** counts SHALL be accurate and match the displayed tasks

#### Scenario: List handles empty task list

**Given** a project with no tasks

**When** the user runs `tasky task list`

**Then** the output SHALL display:
```
No tasks to display
```

**And** no summary line SHALL be displayed

**And** the command SHALL exit with status code 0 (success)

#### Scenario: Long format displays timestamps

**Given** a project with a task created at "2025-11-12T10:30:00Z" and updated at "2025-11-12T14:45:30Z"

**When** the user runs `tasky task list --long`

**Then** each task line SHALL be followed by a timestamp line:
```
○ {task.id} {task.name} - {task.details}
  Created: 2025-11-12T10:30:00Z | Modified: 2025-11-12T14:45:30Z
```

**And** timestamps SHALL be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

**And** timestamp lines SHALL be indented by 2 spaces

**And** both `--long` and `-l` flags SHALL work identically

#### Scenario: Short form flag for long format

**Given** a project with tasks

**When** the user runs `tasky task list -l` (short form)

**Then** the behavior SHALL be identical to `tasky task list --long`

**And** timestamps SHALL be displayed for each task

#### Scenario: List works with status filtering

**Given** a project with 5 pending and 3 completed tasks

**When** the user runs `tasky task list --status pending`

**Then** the output SHALL display only pending tasks

**And** the summary line SHALL reflect filtered counts:
```
Showing 5 tasks (5 pending, 0 completed, 0 cancelled)
```

**And** tasks SHALL still be sorted and formatted with status indicators and IDs

**And** the summary line SHALL indicate that filtering was applied (context preserved from status filter)

#### Scenario: Help text documents output format

**Given** a user running the CLI

**When** the user runs `tasky task list --help`

**Then** the help text SHALL document:
- The output format (status indicator, ID, name, details)
- Status indicator symbols (○, ✓, ✗)
- The meaning of each status indicator
- The `--long` / `-l` flag and its effect
- Example output showing the enhanced format
- How the summary line is displayed

**And** the help text SHALL be clear and user-friendly

---

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

### Requirement: Task Update Command with Positional ID and Optional Field Flags

The system SHALL provide a CLI command `tasky task update TASK_ID [--name NAME] [--details DETAILS]` that updates an existing task's metadata.

**Rationale**: Users need an efficient way to fix typos and update task descriptions after creation. Optional field flags allow flexible, partial updates without requiring users to re-enter unchanged data.

#### Scenario: Update task name only

**Given** a task with ID `3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60`, name "Buy milk", and details "From the store"
**When** the user runs `tasky task update 3af4b92f-c4a1-4b2e-9c3d-7a1b8c2e5f60 --name "Buy organic milk"`
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
**And** special characters (# : & etc.) SHALL be preserved
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

### Requirement: Date Range Filtering on Task Creation Timestamp

The system SHALL support filtering tasks by creation date using `--created-after` and `--created-before` options.

**Rationale**: Users need to focus on recently created tasks or find tasks from specific time periods without manually inspecting timestamps. Date filtering is essential for time-based task organization.

#### Scenario: Filter tasks created after a specific date

**WHEN** the user runs `tasky task list --created-after 2025-01-01`
**THEN** the CLI SHALL display only tasks where `task.created_at >= 2025-01-01T00:00:00Z`
**AND** tasks created before 2025-01-01 SHALL NOT be displayed
**AND** the output format SHALL match existing task list format

#### Scenario: Filter tasks created before a specific date

**WHEN** the user runs `tasky task list --created-before 2025-12-31`
**THEN** the CLI SHALL display only tasks where `task.created_at <= 2025-12-31T23:59:59Z`
**AND** tasks created after 2025-12-31 SHALL NOT be displayed
**AND** the output format SHALL match existing task list format

#### Scenario: Filter tasks within a date range

**WHEN** the user runs `tasky task list --created-after 2025-11-01 --created-before 2025-11-30`
**THEN** the CLI SHALL display only tasks created between 2025-11-01 and 2025-11-30 inclusive
**AND** the filter SHALL use AND logic (both date conditions must match)
**AND** only tasks satisfying both date constraints SHALL appear

#### Scenario: Accept ISO 8601 date format

**WHEN** the user provides dates in ISO 8601 format (YYYY-MM-DD)
**THEN** the system SHALL parse dates correctly
**AND** dates SHALL be interpreted as UTC midnight (00:00:00Z)
**AND** the parsing SHALL NOT fail

#### Scenario: Reject invalid date format with helpful error

**WHEN** the user runs `tasky task list --created-after "Jan 1"` or `--created-after "2025/01/01"`
**THEN** the CLI SHALL display an error message
**AND** the error message SHALL include the expected format "YYYY-MM-DD"
**AND** the error message SHALL include an example like "2025-01-01"
**AND** the CLI SHALL exit with error status code 1
**AND** the CLI SHALL NOT call the task service

---

### Requirement: Text Search in Task Name and Details

The system SHALL support searching tasks by text matching in task name and details fields.

**Rationale**: Users need to find tasks mentioning specific keywords, problem descriptions, or project names without reading every task. Full-text search improves task discovery and navigation.

#### Scenario: Search tasks by text in name

**WHEN** the user runs `tasky task list --search "bug fix"`
**THEN** the CLI SHALL display tasks where "bug fix" appears in the task name
**AND** the search SHALL be case-insensitive
**AND** tasks not containing the search text SHALL NOT be displayed

#### Scenario: Search tasks by text in details

**WHEN** the user runs `tasky task list --search "urgent"`
**THEN** the CLI SHALL display tasks where "urgent" appears in either name or details fields
**AND** all matching fields SHALL be found (OR logic within name+details, AND with other criteria)

#### Scenario: Text search is case-insensitive

**WHEN** the user runs `tasky task list --search "Bug FIX"` or `--search "BUG FIX"`
**THEN** the CLI SHALL match tasks containing "bug fix", "Bug Fix", "BUG FIX", or any case variant
**AND** case sensitivity SHALL NOT affect results

#### Scenario: Text search is substring-based

**WHEN** the user runs `tasky task list --search "bug"`
**THEN** the CLI SHALL match tasks containing "bug", "Bug", "bugfix", "debugging", or any word containing "bug"
**AND** exact word matching SHALL NOT be required
**AND** partial matches SHALL be found

#### Scenario: Empty search text returns all tasks

**WHEN** the user provides `--search ""` (empty string)
**THEN** the CLI SHALL treat it as no search filter
**AND** all tasks SHALL be displayed (unless other filters are applied)

---

### Requirement: Combining Multiple Filter Criteria with AND Logic

The system SHALL support combining multiple filter criteria, with all criteria required to match (AND logic).

**Rationale**: Complex filtering scenarios require combining multiple dimensions (status, date, content). AND logic is intuitive—users expect to narrow results by adding more constraints.

#### Scenario: Filter by status AND date range

**WHEN** the user runs `tasky task list --status pending --created-after 2025-11-01`
**THEN** the CLI SHALL display only tasks that satisfy BOTH conditions:
  - status == TaskStatus.PENDING AND
  - created_at >= 2025-11-01T00:00:00Z
**AND** tasks that are pending but created before 2025-11-01 SHALL NOT appear
**AND** tasks created after 2025-11-01 but not pending SHALL NOT appear

#### Scenario: Filter by status AND search text

**WHEN** the user runs `tasky task list --status pending --search "urgent"`
**THEN** the CLI SHALL display only tasks matching BOTH:
  - status == TaskStatus.PENDING AND
  - name or details contain "urgent" (case-insensitive)
**AND** pending tasks not mentioning "urgent" SHALL NOT appear
**AND** tasks mentioning "urgent" that are not pending SHALL NOT appear

#### Scenario: Filter by date range AND search text

**WHEN** the user runs `tasky task list --created-after 2025-11-01 --created-before 2025-11-30 --search "bug"`
**THEN** the CLI SHALL display only tasks matching ALL three conditions:
  - created_at >= 2025-11-01T00:00:00Z AND
  - created_at <= 2025-11-30T23:59:59Z AND
  - name or details contain "bug"
**AND** the filter SHALL require all conditions to match

#### Scenario: Combine status, date range, AND search text

**WHEN** the user runs `tasky task list --status pending --created-after 2025-11-01 --search "fix"`
**THEN** the CLI SHALL display only tasks matching ALL criteria:
  - status == TaskStatus.PENDING AND
  - created_at >= 2025-11-01T00:00:00Z AND
  - name or details contain "fix"
**AND** each criterion reduces the result set (all must be satisfied)

---

### Requirement: Helpful Error Messages for Invalid Filtering Input

The system SHALL provide clear, actionable error messages when filter criteria are invalid.

**Rationale**: Users will occasionally provide malformed input (wrong date format, invalid status). Clear errors guide toward correct usage and reduce frustration.

#### Scenario: Invalid date format shows expected format

**WHEN** the user runs `tasky task list --created-after "2025-01-01T12:00:00"`
**THEN** the CLI SHALL reject the time component (not supported)
**AND** display an error: "Invalid date format: ... Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)"
**AND** the CLI SHALL exit with status code 1

#### Scenario: Future dates are accepted

**WHEN** the user runs `tasky task list --created-after 2099-12-31`
**THEN** the CLI SHALL accept the date
**AND** no tasks SHALL match (unless created in the far future)
**AND** the CLI SHALL display "No matching tasks found" (not an error)

#### Scenario: Empty result is distinguished from error

**WHEN** filtering produces zero matching tasks
**THEN** the CLI SHALL display "No matching tasks found" (informational)
**AND** the CLI SHALL exit with status code 0 (success)
**AND** the message SHALL differ from error messages

---

### Requirement: Task List Command Complexity Management

The task list command SHALL maintain reasonable cyclomatic complexity through focused helper functions to ensure maintainability and readability.

#### Helper Functions

The tasks.py module SHALL provide the following helpers for list_command:

- `_parse_date_filter(date_str: str, *, inclusive_end: bool) -> datetime`: Parse and validate ISO 8601 dates with timezone handling
- `_build_task_list_filter(...) -> tuple[TaskFilter | None, bool]`: Construct task filter from validated inputs
- `_render_task_list_summary(tasks, has_filters) -> None`: Render "Showing X tasks" summary line

**Complexity Constraints**:
- list_command() SHALL NOT have cyclomatic complexity >10 (no C901 suppression)
- Date parsing logic SHALL NOT be duplicated
- Each helper function SHALL have single, clear responsibility

#### Scenario: Date filter parsing consolidation

```gherkin
Given a user runs "tasky task list --created-after 2025-11-15"
When the validation helper parses the date filter
Then _parse_date_filter() is called with inclusive_end=False
And the returned datetime is timezone-aware UTC
And the time component is 00:00:00 (start of day)
And date validation happens in exactly one location (no duplication)
```

#### Scenario: Inclusive end-of-day handling

```gherkin
Given a user runs "tasky task list --created-before 2025-11-15"
When the validation helper parses the date filter
Then _parse_date_filter() is called with inclusive_end=True
And the returned datetime represents 2025-11-16 00:00:00 UTC
And the filter correctly includes all of 2025-11-15 (exclusive upper bound pattern)
```

#### Scenario: Task list summary rendering

```gherkin
Given a task list contains 5 tasks (2 pending, 2 completed, 1 cancelled)
When _render_task_list_summary() renders the summary
Then the output shows "Showing 5 tasks (2 pending, 2 completed, 1 cancelled)"
And the plural "tasks" is used (not "task")
```

```gherkin
Given a task list contains 1 task
When _render_task_list_summary() renders the summary
Then the output shows "Showing 1 task (...)"
And the singular "task" is used
```

#### Scenario: Empty results with filters

```gherkin
Given a user applies filters that match no tasks
When _render_task_list_summary() is called with empty list and has_filters=True
Then the output shows "No matching tasks found"
And no breakdown line is shown
```

```gherkin
Given a user lists tasks with no filters and project has no tasks
When _render_task_list_summary() is called with empty list and has_filters=False
Then the output shows "No tasks to display"
And no breakdown line is shown
```

---

### Requirement: CLI Error Handling Completeness

All CLI commands SHALL have comprehensive error handling with clear, actionable messages. Error paths SHALL be tested and validated. No unhandled exceptions SHALL reach the user.

#### Scenario: Task not found error is handled gracefully
- **WHEN** user runs `tasky task show <non-existent-id>`
- **THEN** CLI catches the `TaskNotFoundError`
- **AND** displays user-friendly message: "Error: Task '<id>' not found"
- **AND** exits with code 1 (not code 2 or uncaught exception)

#### Scenario: Invalid task ID format is validated
- **WHEN** user runs `tasky task show "not-a-uuid"`
- **THEN** CLI validates input format before service invocation
- **AND** displays: "Error: Invalid task ID: must be a valid UUID"
- **AND** exits with code 1

#### Scenario: Invalid status transition is rejected
- **WHEN** user attempts to complete an already-completed task
- **THEN** CLI catches `InvalidStateTransitionError`
- **AND** suggests valid transitions: "Valid transitions: reopen"
- **AND** exits with code 1

#### Scenario: Storage error is handled appropriately
- **WHEN** database write fails (disk full, permission denied)
- **THEN** CLI catches storage exception
- **AND** displays appropriate message (not raw stack trace)
- **AND** suggests recovery action if available
- **AND** exits with code 2 (internal error)

### Requirement: Import/Export Edge Case Handling

Import and export operations SHALL handle edge cases robustly without data loss.

#### Scenario: Import from malformed file
- **WHEN** user runs `tasky task import broken.json` with invalid JSON
- **THEN** import fails with clear error message
- **AND** no tasks are modified (all-or-nothing)
- **AND** user is told what is wrong with the file

#### Scenario: Import with duplicate task IDs using merge strategy
- **WHEN** importing tasks with IDs that already exist, using merge strategy
- **THEN** system identifies conflicts and resolves them
- **AND** user is informed how many conflicts were resolved
- **AND** original task values are preserved (or explicitly overwritten if user chose replace strategy)

#### Scenario: Large import (10,000+ tasks)
- **WHEN** importing a large task file
- **THEN** operation completes without memory exhaustion
- **AND** progress is shown to user
- **AND** final task count matches imported count

#### Scenario: Export is re-importable
- **WHEN** user exports tasks and then imports them back
- **THEN** all task fields are preserved
- **AND** export file is valid JSON
- **AND** import succeeds with strategy=skip (no duplicates)

### Requirement: CLI Input Validation

CLI commands SHALL validate user input before invoking services, providing immediate feedback for format errors.

#### Scenario: Validation happens before service creation
- **WHEN** user provides invalid input (malformed UUID, invalid date)
- **THEN** validation layer rejects input immediately
- **AND** service is never created (fail-fast)
- **AND** error message is user-friendly

#### Scenario: Validator provides actionable feedback
- **WHEN** user provides date in wrong format
- **THEN** validator returns specific message: "Invalid date format: use YYYY-MM-DD"
- **AND** example is provided: "(e.g., 2025-12-31)"
- **AND** user knows exactly how to correct the input

