# Spec Delta: project-cli-operations

## ADDED Requirements

### Requirement: Project CLI Error Handling Infrastructure

The project CLI commands SHALL provide a centralized error handling infrastructure matching the pattern established in task CLI commands to ensure consistent error presentation and user experience across all CLI operations.

#### Error Handling Components

The projects.py module SHALL provide:

- `Handler` protocol: Type definition for exception handler functions
- `with_project_error_handling` decorator: Wraps commands to catch and handle exceptions
- `render_error(message, suggestion, *, verbose, exc)`: Render error message with optional suggestion and stack trace
- `dispatch_exception(exc, *, verbose)`: Route exception to appropriate handler
- `route_exception_to_handler(exc, *, verbose)`: Determine which handler to use for exception type
- Specialized handler functions for each exception type:
  - `handle_project_not_found`
  - `handle_backend_not_registered`
  - `handle_storage_error`
  - `handle_validation_error`
  - `handle_generic_error`

**Error Handling Principles:**
- All handlers SHALL call `render_error()` for consistent error output
- Verbose mode SHALL show full stack trace when `--verbose` flag is provided
- Non-verbose mode SHALL show user-friendly message + contextual suggestion
- Exit codes SHALL be consistent: 1 for user errors, 3 for storage errors
- All commands SHALL use decorator instead of inline try/except blocks

#### Scenario: Decorator centralizes error handling

```gherkin
Given a project command is decorated with @with_project_error_handling
When the command raises any exception
Then the decorator catches the exception
And routes it to the appropriate handler via dispatch_exception
And the handler renders a user-friendly error message
And the CLI exits with the appropriate exit code
And the command function itself contains no try/except blocks
```

#### Scenario: Verbose mode provides debugging information

```gherkin
Given a project command fails with a storage error
And the user runs the command with --verbose flag
When the error handler renders the error
Then the output includes the user-friendly error message
And the output includes "Detailed error:" section
And the output includes the full stack trace
And the CLI exits with code 3
```

#### Scenario: Backend not registered error provides helpful suggestions

```gherkin
Given a user runs "tasky project init --backend invalid_backend"
When the error handler handles BackendNotRegisteredError
Then the error message includes "Backend 'invalid_backend' not registered"
And the suggestion includes "Available backends: json, sqlite"
And the CLI exits with code 1
```

#### Scenario: Project not found error suggests listing projects

```gherkin
Given a user runs "tasky project info --project-name nonexistent"
When the error handler handles ProjectNotFoundError
Then the error message includes "Project 'nonexistent' not found in registry"
And the suggestion includes "Run 'tasky project list' to see all registered projects"
And the CLI exits with code 1
```

#### Scenario: Storage errors use distinct exit code

```gherkin
Given a project command fails with a StorageError
When the error handler processes the error
Then the error message includes "Storage operation failed"
And the suggestion includes "Check file permissions and disk space"
And the CLI exits with code 3 (not code 1)
```

---

### Requirement: Verbose Mode Support for Project Commands

All project CLI commands SHALL support a `--verbose` flag to provide detailed error information for debugging purposes, matching the verbose mode behavior of task commands.

#### Verbose Flag Specification

Each project command SHALL accept:
- `--verbose` / `-v`: Boolean flag to enable verbose error output
- Default: False (non-verbose mode)

**Verbose Mode Behavior:**
- Non-verbose: Show user-friendly error message with contextual suggestion
- Verbose: Show user-friendly message + suggestion + full Python stack trace

#### Scenario: All project commands support verbose flag

```gherkin
Given the project CLI commands (init, info, list, register, unregister, discover)
When a user runs any command with --verbose flag
Then the command accepts the flag without error
And if an error occurs, the full stack trace is displayed
And the verbose flag does not affect command behavior in success case
```

#### Scenario: Verbose mode helps diagnose configuration issues

```gherkin
Given a project has a corrupted config.toml file
And the user runs "tasky project info --verbose"
When the command fails to load the configuration
Then the error output includes the user-friendly message
And the error output includes the full stack trace showing where parsing failed
And the user can identify the specific line in config.toml causing the issue
```

---

### Requirement: Exception Type Routing

The project CLI error handling SHALL route exceptions to specialized handlers based on exception type to provide contextual error messages and suggestions appropriate to each error category.

#### Exception Routing Rules

The error dispatcher SHALL route exceptions as follows:

| Exception Type | Handler | Exit Code | Suggestion Pattern |
|----------------|---------|-----------|-------------------|
| ProjectNotFoundError | handle_project_not_found | 1 | "Run 'tasky project list' to see..." |
| BackendNotRegisteredError | handle_backend_not_registered | 1 | "Available backends: ..." |
| StorageError | handle_storage_error | 3 | "Check file permissions..." |
| ValueError, TypeError | handle_validation_error | 1 | (error-specific) |
| Other exceptions | handle_generic_error | 1 | "Use --verbose for details" |

**Routing Behavior:**
- `typer.Exit` exceptions SHALL be re-raised without handling
- Handlers SHALL provide actionable suggestions based on error context
- Error messages SHALL be concise and non-technical for non-verbose mode

#### Scenario: Each exception type routes to correct handler

```gherkin
Given a command wrapped with @with_project_error_handling
When the command raises ProjectNotFoundError
Then dispatch_exception routes to handle_project_not_found
And the error is rendered with project-specific suggestions
And the CLI exits with code 1
```

```gherkin
Given a command wrapped with @with_project_error_handling
When the command raises StorageError
Then dispatch_exception routes to handle_storage_error
And the error is rendered with storage-specific suggestions
And the CLI exits with code 3
```

---

## MODIFIED Requirements

None. This change adds error handling infrastructure without modifying existing project command requirements.

---

## REMOVED Requirements

None. All existing project command requirements are preserved.
