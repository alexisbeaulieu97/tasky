## ADDED Requirements

### Conventions (Required)

This change MUST follow project patterns:
- **Model-driven validation**: Validation happens by attempting to create/parse Pydantic models. CLI catches `ValidationError` and displays user-friendly messages.
- **No separate Validator protocol**: Don't create a standalone validation system. Use Pydantic `@field_validator` on models.
- **ValidationResult usage**: Only as a light wrapper if needed for CLI-specific validation beyond model creation. Prefer raising Pydantic `ValidationError`.
- **Typer integration**: Use `typer.Option()` with type hints; Typer and Pydantic handle validation together.

### Requirement: Input Validation Framework

The CLI SHALL provide a `Validator` protocol and concrete implementations for validating user input before service invocation. Each validator SHALL return a `ValidationResult[T]` containing either a valid typed value or a user-friendly error message.

#### ValidationResult[T] Structure

The `ValidationResult[T]` MUST be implemented as a generic dataclass-like object (using `@dataclass` or Pydantic) with the following contract:

**Fields:**
- `is_valid: bool` — True if validation succeeded, False otherwise
- `value: T | None` — The validated value (only set if `is_valid=True`)
- `error_message: str | None` — User-friendly error message (only set if `is_valid=False`)

**Factory Methods (classmethods):**
- `ValidationResult.success(value: T) → ValidationResult[T]` — Construct a successful result with a value
- `ValidationResult.failure(message: str) → ValidationResult[T]` — Construct a failed result with an error message

**Validation Constraint:**
- Validators MUST NOT raise exceptions; they MUST always return a `ValidationResult` object
- Callers MUST check `result.is_valid` before accessing `result.value`
- If `is_valid=False`, callers MUST read `result.error_message` for display/logging

#### Scenario: Validator accepts valid input
- **WHEN** a validator receives input matching its format (e.g., valid UUID, ISO date)
- **THEN** it SHALL return `ValidationResult.success(value)`
- **AND** the caller can use the validated value with confidence

#### Scenario: Validator rejects invalid input
- **WHEN** a validator receives malformed input (e.g., non-UUID string, invalid date)
- **THEN** it SHALL return `ValidationResult.failure(message)`
- **AND** the message SHALL be suitable for direct display to users (e.g., "Invalid task ID: not a UUID")

### Requirement: Task ID Validation

The system SHALL validate task IDs as UUID format before invoking service methods.

#### Scenario: Valid UUID accepted
- **WHEN** user provides a valid UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
- **THEN** validator SHALL accept it and return typed UUID

#### Scenario: Invalid UUID rejected
- **WHEN** user provides non-UUID string (e.g., "abc123" or empty string)
- **THEN** validator SHALL reject with message: "Invalid task ID: must be a valid UUID"

### Requirement: Date Validation

The system SHALL validate dates in ISO 8601 format before applying to task fields.

#### Scenario: Valid ISO date accepted
- **WHEN** user provides date in format YYYY-MM-DD (e.g., "2025-12-31")
- **THEN** validator SHALL accept and return date object

#### Scenario: Invalid date format rejected
- **WHEN** user provides malformed date (e.g., "31/12/2025" or "tomorrow")
- **THEN** validator SHALL reject with message: "Invalid date format: use YYYY-MM-DD (e.g., 2025-12-31)"

### Requirement: Status Validation

The system SHALL validate task status against allowed values before updating.

#### Scenario: Valid status accepted
- **WHEN** user specifies status "todo", "in_progress", or "completed"
- **THEN** validator SHALL accept and return status enum value

#### Scenario: Invalid status rejected
- **WHEN** user specifies unknown status (e.g., "in progress" with space or "done")
- **THEN** validator SHALL reject with message listing valid options: "Invalid status. Choose from: todo, in_progress, completed"

### Requirement: Priority Validation

The system SHALL validate task priority against allowed values.

#### Scenario: Valid priority accepted
- **WHEN** user specifies priority "low", "normal", or "high"
- **THEN** validator SHALL accept and return priority enum value

#### Scenario: Invalid priority rejected
- **WHEN** user specifies unknown priority (e.g., "critical" or "1")
- **THEN** validator SHALL reject with message: "Invalid priority. Choose from: low, normal, high"

### Requirement: Validation Integration in CLI Commands

The CLI commands SHALL invoke validators for user input before calling service methods, reducing redundant checks and improving error consistency.

#### Scenario: Command validates input early
- **WHEN** user runs `tasky task show invalid-id`
- **THEN** CLI SHALL validate the ID with `TaskIdValidator`
- **AND** if validation fails, display error and exit without creating services

#### Scenario: Command passes validated value to service
- **WHEN** validation succeeds, user input is confirmed valid
- **THEN** command SHALL invoke service method with validated value
- **AND** service need not re-validate format (but may validate business rules)
