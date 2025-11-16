## MODIFIED Requirements

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
