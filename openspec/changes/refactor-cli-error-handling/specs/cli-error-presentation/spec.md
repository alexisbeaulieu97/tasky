## MODIFIED Requirements

### Requirement: CLI Exception Handling Dispatcher

The CLI SHALL catch domain exceptions and present clear, actionable messages using a centralized error dispatcher that routes exceptions to appropriate handlers. It SHALL hide technical details (stack traces, exception types) in normal operation, SHALL use language appropriate for end users (not developers), and SHALL provide context about what operation failed and why.

The error dispatcher SHALL:
- Implement a registry-based pattern where handlers register for specific exception types
- Provide a single `dispatch(exc: Exception, verbose: bool) -> str` method that routes to the appropriate handler
- Include handlers for domain exceptions (`TaskNotFoundError`, `TaskValidationError`, `InvalidStateTransitionError`), storage errors, and project-related errors
- Return user-friendly error messages for all registered exception types
- Provide a fallback handler for unexpected exceptions

#### Scenario: Domain exception caught and formatted
- **GIVEN** a user runs `tasky task show <non-existent-id>`
- **WHEN** a `TaskNotFoundError` is raised
- **THEN** the dispatcher SHALL route to the task domain handler
- **AND** the CLI SHALL display: "Error: Task '<id>' not found"
- **AND** SHALL NOT display a Python stack trace
- **AND** SHALL exit with code 1

#### Scenario: Storage exception caught and formatted
- **GIVEN** a task operation fails in the storage layer
- **WHEN** a storage-related exception is raised (e.g., permission denied, disk full)
- **THEN** the dispatcher SHALL route to the storage error handler
- **AND** the CLI SHALL display: "Error: Storage operation failed: <message>"
- **AND** SHALL exit with code 1

#### Scenario: Validation exception caught and formatted
- **GIVEN** a user attempts an operation that raises `TaskValidationError`
- **WHEN** the exception is caught by the dispatcher
- **THEN** the dispatcher SHALL route to the task domain handler
- **AND** the CLI SHALL display: "Error: <validation-message>"
- **AND** SHALL provide guidance on fixing the issue if available
- **AND** SHALL exit with code 1

#### Scenario: Invalid state transition caught and formatted
- **GIVEN** a user attempts to transition a task to an invalid state
- **WHEN** an `InvalidStateTransitionError` is raised
- **THEN** the dispatcher SHALL route to the task domain handler
- **AND** the CLI SHALL display: "Error: Cannot transition task from <from> to <to>"
- **AND** SHALL suggest valid transitions
- **AND** SHALL exit with code 1

#### Scenario: Unexpected exception falls back to generic handler
- **GIVEN** an exception type not registered in the dispatcher is raised
- **WHEN** the dispatcher receives the exception
- **THEN** the fallback handler SHALL be invoked
- **AND** the CLI SHALL display: "Error: An unexpected error occurred"
- **AND** in verbose mode, additional context MAY be provided
- **AND** SHALL exit with code 2 (indicating internal error)
