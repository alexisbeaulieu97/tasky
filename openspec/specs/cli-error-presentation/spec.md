# cli-error-presentation Specification

## Purpose

Defines how the Tasky CLI presents errors to users, maps exceptions to user-friendly messages, and provides appropriate exit codes for different failure scenarios.

## Requirements
### Requirement: User-Friendly Error Messages


The CLI SHALL catch domain exceptions and present clear, actionable messages. It SHALL hide technical details (stack traces, exception types) in normal operation, SHALL use language appropriate for end users (not developers), and SHALL provide context about what operation failed and why.

#### Scenario: Task not found message

**Given** a user runs `tasky task show <non-existent-id>`  
**When** a `TaskNotFoundError` is raised  
**Then** the CLI SHALL display: "Error: Task '<id>' not found"  
**And** SHALL NOT display a Python stack trace  
**And** SHALL exit with code 1

#### Scenario: Validation error message

**Given** a user attempts an operation that raises `TaskValidationError`  
**When** the exception is caught by the CLI  
**Then** the CLI SHALL display: "Error: <validation-message>"  
**And** SHALL provide guidance on fixing the issue if available  
**And** SHALL exit with code 1

#### Scenario: State transition error message

**Given** a user attempts to transition a task to an invalid state  
**When** an `InvalidStateTransitionError` is raised  
**Then** the CLI SHALL display: "Error: Cannot transition task from <from> to <to>"  
**And** SHALL suggest valid transitions  
**And** SHALL exit with code 1


### Requirement: Appropriate Exit Codes


The CLI SHALL exit with code 0 for successful operations, SHALL exit with code 1 for domain errors (business rule violations), SHALL exit with code 2 for CLI usage errors (invalid arguments), and SHALL exit with code 3 for infrastructure errors (storage failures).

#### Scenario: Success exit code

**Given** a successful task operation  
**When** the command completes  
**Then** the CLI SHALL exit with code 0

#### Scenario: Domain error exit code

**Given** a `TaskNotFoundError` or `TaskValidationError` is raised  
**When** the CLI handles the error  
**Then** the CLI SHALL exit with code 1

#### Scenario: Storage error exit code

**Given** a `StorageError` is raised  
**When** the CLI handles the error  
**Then** the CLI SHALL exit with code 3  
**And** MAY suggest checking file permissions or paths


### Requirement: Error Handler Centralization


The CLI SHALL implement error handling consistently across all commands, SHALL avoid duplicated error handling code, SHALL use decorators or context managers for common error patterns, and SHALL handle unexpected errors gracefully with a generic message.

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
**And** SHALL exit with code 1


### Requirement: Verbose Error Mode


The CLI SHALL support a `--verbose` or `-v` flag for detailed error output, SHALL display full stack traces when verbose mode is enabled, SHALL include exception types and context in verbose output, and SHALL default to user-friendly messages without the verbose flag.

#### Scenario: Normal error output

**Given** verbose mode is NOT enabled  
**When** a domain exception is raised  
**Then** only the user-friendly message SHALL be displayed  
**And** stack traces SHALL be hidden

#### Scenario: Verbose error output

**Given** verbose mode IS enabled (`--verbose` flag)  
**When** a domain exception is raised  
**Then** the full stack trace SHALL be displayed  
**And** exception type and context SHALL be shown  
**And** developers can debug the issue


### Requirement: Error Message Formatting


Error messages SHALL start with an "Error: " prefix for clarity, SHALL use consistent formatting across all commands, SHALL highlight key information (task IDs, statuses) if the terminal supports it, and SHALL keep messages concise (≤2 lines when possible).

#### Scenario: Error message structure

**Given** any CLI error message  
**When** displayed to the user  
**Then** it SHALL start with "Error: " or "Warning: "  
**And** SHALL use consistent sentence structure  
**And** SHALL NOT end with technical jargon

#### Scenario: Terminal color support

**Given** the terminal supports ANSI colors  
**When** an error is displayed  
**Then** "Error: " MAY be colored red  
**And** key values (IDs, statuses) MAY be highlighted  
**And** messages remain readable if colors are disabled


### Requirement: Actionable Error Guidance


Error messages SHALL suggest next steps when possible, SHALL reference valid options for invalid inputs, SHALL provide command examples for common mistakes, and SHALL link to help or documentation when appropriate.

#### Scenario: Invalid task ID format

**Given** a user provides an invalid task ID format  
**When** a validation error occurs  
**Then** the error SHALL suggest the correct ID format  
**And** MAY provide an example: "Use: tasky task show <uuid>"

#### Scenario: No project initialized

**Given** a user runs a task command outside a Tasky project  
**When** a `ProjectNotFoundError` is raised  
**Then** the error SHALL suggest: "Run 'tasky project init' first"


### Requirement: Error Context Preservation


When handling exceptions, the CLI SHALL extract context from exception attributes (task_id, status, etc.), SHALL use context to personalize error messages, SHALL preserve context for logging (future), and SHALL not rely solely on exception message strings.

#### Scenario: Using exception context

**Given** a `TaskNotFoundError` with `task_id = 'abc-123'`  
**When** formatting the error message  
**Then** the CLI SHALL extract `task_id` from exception attributes  
**And** include it in the formatted message: "Task 'abc-123' not found"

