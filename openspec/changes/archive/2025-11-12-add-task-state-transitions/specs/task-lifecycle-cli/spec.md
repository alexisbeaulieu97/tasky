# Spec: Task Lifecycle CLI Commands

**Capability ID**: `task-lifecycle-cli`  
**Status**: New Capability  
**Related Changes**: `add-task-state-transitions`

---

## ADDED Requirements

### Requirement: CLI SHALL Provide Complete Task Command
**ID**: `REQ-TLCLI-001`  
**Priority**: Must Have

The CLI MUST provide a command to mark tasks as completed.

#### Scenario: Complete command with valid task
**Given** a pending task exists with ID "abc-123" and name "Write tests"  
**When** the user runs `tasky task complete abc-123`  
**Then** the task status changes to "completed"  
**And** a success message is displayed: "✓ Task 'Write tests' completed"  
**And** the command exits with code 0

#### Scenario: Complete command accepts UUID in any format
**Given** a pending task exists with UUID "123e4567-e89b-12d3-a456-426614174000"  
**When** the user runs `tasky task complete 123e4567-e89b-12d3-a456-426614174000`  
**Then** the task is marked as completed  
**And** the command succeeds

#### Scenario: Complete command with invalid UUID
**Given** the user provides invalid task ID "not-a-uuid"  
**When** the user runs `tasky task complete not-a-uuid`  
**Then** an error message is displayed: "Invalid task ID format"  
**And** the command exits with code 1

#### Scenario: Complete command with non-existent task
**Given** no task exists with ID "nonexistent-id"  
**When** the user runs `tasky task complete nonexistent-id`  
**Then** an error message is displayed: "Task not found: nonexistent-id"  
**And** the command exits with code 1

#### Scenario: Complete command with already completed task
**Given** a task exists with ID "abc-123" and status "completed"  
**When** the user runs `tasky task complete abc-123`  
**Then** an error message is displayed explaining the task is already completed  
**And** the command exits with code 1

#### Scenario: Complete command shows help
**Given** no arguments are provided  
**When** the user runs `tasky task complete --help`  
**Then** help text is displayed explaining the command usage  
**And** includes description: "Mark a task as completed"  
**And** shows argument: "<task-id> - Task ID to complete"

---

### Requirement: CLI SHALL Provide Cancel Task Command
**ID**: `REQ-TLCLI-002`  
**Priority**: Must Have

The CLI MUST provide a command to cancel tasks.

#### Scenario: Cancel command with valid task
**Given** a pending task exists with ID "abc-123" and name "Old feature"  
**When** the user runs `tasky task cancel abc-123`  
**Then** the task status changes to "cancelled"  
**And** a success message is displayed: "✓ Task 'Old feature' cancelled"  
**And** the command exits with code 0

#### Scenario: Cancel command with completed task shows guidance
**Given** a task exists with ID "abc-123" and status "completed"  
**When** the user runs `tasky task cancel abc-123`  
**Then** an error message is displayed: "Cannot cancel completed task"  
**And** the message suggests: "Use 'tasky task reopen abc-123' to make it pending again"  
**And** the command exits with code 1

#### Scenario: Cancel command with non-existent task
**Given** no task exists with ID "nonexistent-id"  
**When** the user runs `tasky task cancel nonexistent-id`  
**Then** an error message is displayed: "Task not found: nonexistent-id"  
**And** the command exits with code 1

#### Scenario: Cancel command with already cancelled task
**Given** a task exists with ID "abc-123" and status "cancelled"  
**When** the user runs `tasky task cancel abc-123`  
**Then** an error message is displayed explaining the task is already cancelled  
**And** the command exits with code 1

#### Scenario: Cancel command shows help
**Given** no arguments are provided  
**When** the user runs `tasky task cancel --help`  
**Then** help text is displayed explaining the command usage  
**And** includes description: "Mark a task as cancelled"  
**And** shows argument: "<task-id> - Task ID to cancel"

---

### Requirement: CLI SHALL Provide Reopen Task Command
**ID**: `REQ-TLCLI-003`  
**Priority**: Must Have

The CLI MUST provide a command to reopen completed or cancelled tasks.

#### Scenario: Reopen completed task
**Given** a completed task exists with ID "abc-123" and name "Review PR"  
**When** the user runs `tasky task reopen abc-123`  
**Then** the task status changes to "pending"  
**And** a success message is displayed: "✓ Task 'Review PR' reopened"  
**And** the command exits with code 0

#### Scenario: Reopen cancelled task
**Given** a cancelled task exists with ID "abc-123" and name "Deploy feature"  
**When** the user runs `tasky task reopen abc-123`  
**Then** the task status changes to "pending"  
**And** a success message is displayed: "✓ Task 'Deploy feature' reopened"  
**And** the command exits with code 0

#### Scenario: Reopen pending task shows error
**Given** a task exists with ID "abc-123" and status "pending"  
**When** the user runs `tasky task reopen abc-123`  
**Then** an error message is displayed: "Cannot reopen pending task"  
**And** the message explains: "Task is already pending"  
**And** the command exits with code 1

#### Scenario: Reopen non-existent task
**Given** no task exists with ID "nonexistent-id"  
**When** the user runs `tasky task reopen nonexistent-id`  
**Then** an error message is displayed: "Task not found: nonexistent-id"  
**And** the command exits with code 1

#### Scenario: Reopen command shows help
**Given** no arguments are provided  
**When** the user runs `tasky task reopen --help`  
**Then** help text is displayed explaining the command usage  
**And** includes description: "Reopen a completed or cancelled task"  
**And** shows argument: "<task-id> - Task ID to reopen"

---

### Requirement: State Transition Commands MUST Be Discoverable
**ID**: `REQ-TLCLI-004`  
**Priority**: Must Have

State transition commands MUST be discoverable through the CLI help system.

#### Scenario: Task commands listed in main help
**Given** the CLI is installed  
**When** the user runs `tasky task --help`  
**Then** the help output lists all task commands  
**And** includes "complete" with brief description  
**And** includes "cancel" with brief description  
**And** includes "reopen" with brief description

#### Scenario: Commands follow consistent naming
**Given** all task lifecycle commands  
**Then** they use verb-based names: "complete", "cancel", "reopen"  
**And** they all accept a single argument: task ID  
**And** they all follow pattern: `tasky task <verb> <task-id>`

---

### Requirement: Error Messages MUST Be Clear and Actionable
**ID**: `REQ-TLCLI-005`  
**Priority**: Must Have

Error messages MUST be clear, actionable, and user-friendly.

#### Scenario: Error messages use simple language
**Given** any error condition in state transition commands  
**When** an error message is displayed  
**Then** it uses plain English without technical jargon  
**And** it does not show Python stack traces  
**And** it does not expose internal class names or implementation details

#### Scenario: Error messages suggest solutions
**Given** an invalid state transition is attempted  
**When** the error message is displayed  
**Then** it explains why the operation failed  
**And** it suggests what the user should do instead  
**And** it includes the command to run if applicable

**Examples**:
- "Cannot cancel completed task. Use 'tasky task reopen abc-123' to make it pending again."
- "Cannot complete cancelled task. Use 'tasky task reopen abc-123' first."
- "Task is already completed."

#### Scenario: Error messages include relevant context
**Given** an operation fails  
**When** the error message is displayed  
**Then** it includes the task ID that was provided  
**And** it includes the current task status when relevant  
**And** it avoids dumping excessive information

---

### Requirement: Commands SHALL Use Consistent Exit Codes
**ID**: `REQ-TLCLI-006`  
**Priority**: Must Have

Commands MUST use consistent exit codes to enable scripting and automation.

#### Scenario: Success returns exit code 0
**Given** any successful state transition command  
**When** the command completes successfully  
**Then** the exit code is 0

#### Scenario: Domain errors return exit code 1
**Given** a state transition command that fails due to business rules  
**When** the command fails with `TaskNotFoundError` or `InvalidStateTransitionError`  
**Then** the exit code is 1

#### Scenario: Storage errors return exit code 3
**Given** a state transition command that fails due to storage issues  
**When** the command fails with any `StorageError`  
**Then** the exit code is 3  
**Note**: This aligns with broader error handling strategy in `add-domain-exception-hierarchy`

#### Scenario: Invalid arguments return exit code 2
**Given** a state transition command with invalid arguments  
**When** the command fails due to UUID parsing or missing arguments  
**Then** the exit code is 2

---

## Dependencies

### Upstream Dependencies (Required Before This)
- **task-state-transitions**: Provides service methods (`complete_task`, `cancel_task`, `reopen_task`)
- **add-domain-exception-hierarchy**: Provides `TaskNotFoundError` and `InvalidStateTransitionError`

### Downstream Dependencies (Enabled By This)
- Task automation scripts can use exit codes for control flow
- Future interactive CLI features can build on command consistency

---

## Acceptance Criteria

1. **Commands Available**: `tasky task complete`, `cancel`, and `reopen` all work end-to-end
2. **Help Text**: All commands have clear help text accessible via `--help`
3. **Error Handling**: All error scenarios display user-friendly messages without stack traces
4. **Exit Codes**: Commands return correct exit codes for scripting support
5. **UUID Parsing**: Commands accept standard UUID format and provide clear errors for invalid input
6. **Success Messages**: Successful operations display confirmation with task name
7. **Discoverability**: Commands appear in `tasky task --help` output
8. **Consistency**: All three commands follow the same usage pattern and conventions

---

## Out of Scope

- Bulk operations (complete multiple tasks at once)
- Interactive confirmation prompts
- Undo functionality
- Task status history display
- Transition notifications or hooks
- Custom completion notes or metadata
- Alias commands (e.g., `done` for `complete`)
