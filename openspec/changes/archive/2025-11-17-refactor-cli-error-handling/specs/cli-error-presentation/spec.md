## MODIFIED Requirements

### Requirement: Error Handler Centralization

The CLI SHALL implement error handling consistently across all commands using a centralized error dispatcher that routes exceptions to appropriate handlers. The CLI SHALL avoid duplicated error handling code, SHALL use decorators or context managers for common error patterns, and SHALL handle unexpected errors gracefully with a generic message.

The error dispatcher SHALL:
- Implement a registry-based pattern where handlers register for specific exception types
- Provide a single `dispatch(exc: Exception, verbose: bool) -> str` method that routes to the appropriate handler
- Include handlers for domain exceptions (`TaskNotFoundError`, `TaskValidationError`, `InvalidStateTransitionError`), storage errors, and project-related errors
- Return user-friendly error messages for all registered exception types
- Provide a fallback handler for unexpected exceptions

#### Scenario: Consistent error handling

**Given** multiple CLI commands that perform task operations
**When** any command encounters a `TaskNotFoundError`
**Then** all commands SHALL present the error identically
**And** use the same exit code

#### Scenario: Unexpected error handling

**Given** an unexpected exception (not domain or storage)
**When** the CLI catches it
**Then** it SHALL display: "An unexpected error occurred"
**And** SHALL suggest filing a bug report
**And** SHALL exit with code 2

#### Scenario: Domain exception caught and formatted

**Given** a user runs `tasky task show <non-existent-id>`
**When** a `TaskNotFoundError` is raised
**Then** the dispatcher SHALL route to the task domain handler
**And** the CLI SHALL display: "Error: Task '<id>' not found"
**And** SHALL NOT display a Python stack trace
**And** SHALL exit with code 1

#### Scenario: Storage exception caught and formatted

**Given** a task operation fails in the storage layer
**When** a storage-related exception is raised (e.g., permission denied, disk full)
**Then** the dispatcher SHALL route to the storage error handler
**And** the CLI SHALL display: "Error: Storage operation failed: <message>"
**And** SHALL exit with code 1

#### Scenario: Validation exception caught and formatted

**Given** a user attempts an operation that raises `TaskValidationError`
**When** the exception is caught by the dispatcher
**Then** the dispatcher SHALL route to the task domain handler
**And** the CLI SHALL display: "Error: <validation-message>"
**And** SHALL provide guidance on fixing the issue if available
**And** SHALL exit with code 1

#### Scenario: Invalid state transition caught and formatted

**Given** a user attempts to transition a task to an invalid state
**When** an `InvalidStateTransitionError` is raised
**Then** the dispatcher SHALL route to the task domain handler
**And** the CLI SHALL display: "Error: Cannot transition task from <from> to <to>"
**And** SHALL suggest valid transitions
**And** SHALL exit with code 1

#### Scenario: Unexpected exception falls back to generic handler

**Given** an exception type not registered in the dispatcher is raised
**When** the dispatcher receives the exception
**Then** the fallback handler SHALL be invoked
**And** the CLI SHALL display: "Error: An unexpected error occurred"
**And** in verbose mode, additional context MAY be provided
**And** SHALL exit with code 2 (indicating internal error)
