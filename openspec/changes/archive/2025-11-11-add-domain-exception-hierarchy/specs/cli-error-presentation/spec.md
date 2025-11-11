# Specification: CLI Error Presentation

**Capability**: `cli-error-presentation`  
**Status**: Draft  
**Created**: 2025-11-11

## Overview

Defines how the Tasky CLI presents errors to users, maps exceptions to user-friendly messages, and provides appropriate exit codes for different failure scenarios.

---

## ADDED Requirements

### Requirement: User-Friendly Error Messages

**ID**: `cli-error-presentation-messages`  
**Priority**: High  
**Type**: Functional

The CLI SHALL:
1. Catch domain exceptions and present clear, actionable messages
2. Hide technical details (stack traces, exception types) in normal operation
3. Use language appropriate for end users, not developers
4. Provide context about what operation failed and why

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

---

### Requirement: Appropriate Exit Codes

**ID**: `cli-error-presentation-exit-codes`  
**Priority**: High  
**Type**: Functional

The CLI SHALL:
1. Exit with code 0 for successful operations
2. Exit with code 1 for domain errors (business rule violations)
3. Exit with code 2 for CLI usage errors (invalid arguments)
4. Exit with code 3 for infrastructure errors (storage failures)

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

---

### Requirement: Error Handler Centralization

**ID**: `cli-error-presentation-centralization`  
**Priority**: Medium  
**Type**: Architectural

The CLI SHALL:
1. Implement error handling consistently across all commands
2. Avoid duplicated error handling code
3. Use decorators or context managers for common error patterns
4. Handle unexpected errors gracefully with generic message

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

---

### Requirement: Verbose Error Mode

**ID**: `cli-error-presentation-verbose`  
**Priority**: Low  
**Type**: Functional

The CLI SHALL:
1. Support a `--verbose` or `-v` flag for detailed error output
2. Display full stack traces when verbose mode is enabled
3. Include exception types and context in verbose output
4. Default to user-friendly messages without verbose flag

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

---

### Requirement: Error Message Formatting

**ID**: `cli-error-presentation-formatting`  
**Priority**: Medium  
**Type**: Non-Functional

Error messages SHALL:
1. Start with "Error: " prefix for clarity
2. Use consistent formatting across all commands
3. Highlight key information (task IDs, statuses) if terminal supports it
4. Keep messages concise (≤2 lines when possible)

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

---

### Requirement: Actionable Error Guidance

**ID**: `cli-error-presentation-guidance`  
**Priority**: Medium  
**Type**: Functional

Error messages SHALL:
1. Suggest next steps when possible
2. Reference valid options for invalid inputs
3. Provide command examples for common mistakes
4. Link to help or documentation when appropriate

#### Scenario: Invalid task ID format

**Given** a user provides an invalid task ID format  
**When** a validation error occurs  
**Then** the error SHALL suggest the correct ID format  
**And** MAY provide an example: "Use: tasky task show <uuid>"

#### Scenario: No project initialized

**Given** a user runs a task command outside a Tasky project  
**When** a `ProjectNotFoundError` is raised  
**Then** the error SHALL suggest: "Run 'tasky project init' first"

---

### Requirement: Error Context Preservation

**ID**: `cli-error-presentation-context`  
**Priority**: Low  
**Type**: Functional

When handling exceptions, the CLI SHALL:
1. Extract context from exception attributes (task_id, status, etc.)
2. Use context to personalize error messages
3. Preserve context for logging (future)
4. Not rely solely on exception message strings

#### Scenario: Using exception context

**Given** a `TaskNotFoundError` with `task_id = 'abc-123'`  
**When** formatting the error message  
**Then** the CLI SHALL extract `task_id` from exception attributes  
**And** include it in the formatted message: "Task 'abc-123' not found"

---

## MODIFIED Requirements

None (no existing CLI error handling to modify)

---

## Design Notes

### Error Handling Strategy

**Three-Layer Approach**:

1. **Command Level**: Specific handlers for command-specific scenarios
2. **App Level**: Generic handlers for common exceptions
3. **Global Level**: Catch-all for unexpected errors

```python
@task_app.command()
def delete_command(task_id: str):
    try:
        # Command logic
        pass
    except TaskNotFoundError as e:
        # Specific handler
        typer.echo(f"Error: Task '{e.task_id}' not found", err=True)
        raise typer.Exit(1)
    except Exception as e:
        # Fallback handler
        handle_unexpected_error(e)
```

### Exit Code Conventions

| Code | Meaning | Examples |
|------|---------|----------|
| 0 | Success | All operations completed |
| 1 | Domain error | Not found, validation, state transition |
| 2 | Usage error | Invalid arguments, missing required options |
| 3 | Infrastructure | Storage failures, file I/O errors |

Rationale: Follows Unix conventions where 0=success, 1=general error, 2=usage error.

### Message Composition Guidelines

1. **Clarity**: User understands what went wrong
2. **Context**: Include relevant IDs or values
3. **Action**: Suggest what to do next
4. **Brevity**: Keep messages short

**Template**:
```
Error: <What failed>
Suggestion: <How to fix>
```

**Examples**:
- ❌ "Task not found" (no context)
- ✅ "Error: Task 'abc-123' not found"

- ❌ "InvalidStateTransitionError" (technical)
- ✅ "Error: Cannot mark completed task as cancelled"

### Verbose Mode Considerations

Verbose mode is for developers/debugging, not normal users:
- Show full tracebacks
- Include exception types
- Display context attributes
- Reveal internal state

Normal mode is for users:
- Hide technical details
- Use plain language
- Focus on solutions
- Keep output clean

---

## Testing Requirements

### Unit Tests

1. ✅ Error messages formatted correctly for each exception type
2. ✅ Exit codes match expected values
3. ✅ Context extracted from exceptions properly
4. ✅ Verbose mode toggles detailed output

### Integration Tests

1. ✅ End-to-end error handling from service to CLI output
2. ✅ Error messages appear on stderr, not stdout
3. ✅ Commands exit with appropriate codes
4. ✅ User sees actionable messages for common errors

### Acceptance Tests

1. ✅ Non-technical users understand error messages
2. ✅ Error guidance helps users resolve issues
3. ✅ No Python exceptions visible in normal operation

---

## Non-Functional Requirements

- **Usability**: Error messages SHALL be understandable by non-developers
- **Consistency**: Similar errors SHALL produce similar messages
- **Accessibility**: Error messages SHALL work in non-color terminals
- **Localization**: Messages SHALL use consistent terminology for future i18n

---

## Future Considerations

- **Error logging**: Log errors to file for debugging (separate logging change)
- **Error reporting**: Optionally report crashes to telemetry service
- **Rich formatting**: Use Rich library for better terminal output
- **Interactive help**: Suggest commands interactively after errors
