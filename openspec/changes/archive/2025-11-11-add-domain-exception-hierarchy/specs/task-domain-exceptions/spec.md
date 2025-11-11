# Specification: Task Domain Exceptions

**Capability**: `task-domain-exceptions`  
**Status**: Draft  
**Created**: 2025-11-11

## Overview

Defines a structured exception hierarchy for the task domain that enables precise error handling, rich error context, and clear separation between domain violations and infrastructure failures.

---

## ADDED Requirements

### Requirement: Base Domain Exception

**ID**: `task-domain-exceptions-base`  
**Priority**: High  
**Type**: Functional

The task domain SHALL provide a base exception class that:
1. Serves as the parent for all task-related domain exceptions
2. Inherits from Python's `Exception` class
3. Allows catching all domain exceptions with a single handler
4. Distinguishes domain violations from infrastructure errors

#### Scenario: Catching all domain errors

**Given** a service operation that may raise various domain exceptions  
**When** the caller wraps the operation in a try-except block  
**Then** catching `TaskDomainError` SHALL catch all domain-specific exceptions  
**And** the exception type can be inspected for specific handling

---

### Requirement: Task Not Found Exception

**ID**: `task-domain-exceptions-not-found`  
**Priority**: High  
**Type**: Functional

The task domain SHALL provide a `TaskNotFoundError` exception that:
1. Inherits from `TaskDomainError`
2. Includes the `task_id` that was not found
3. Provides a clear, human-readable default message
4. Is raised when operations reference non-existent tasks

#### Scenario: Task lookup fails

**Given** a repository with tasks having IDs `[a, b, c]`  
**When** the service attempts to retrieve task with ID `d`  
**Then** a `TaskNotFoundError` SHALL be raised  
**And** the exception SHALL contain `task_id = d`  
**And** the exception message SHALL indicate which task was not found

#### Scenario: Task deletion fails

**Given** a repository with no task having ID `xyz`  
**When** the service attempts to delete task `xyz`  
**Then** a `TaskNotFoundError` SHALL be raised  
**And** the exception SHALL include the task_id `xyz`

---

### Requirement: Task Validation Exception

**ID**: `task-domain-exceptions-validation`  
**Priority**: High  
**Type**: Functional

The task domain SHALL provide a `TaskValidationError` exception that:
1. Inherits from `TaskDomainError`
2. Includes a descriptive message about what failed validation
3. Optionally includes the field name that failed validation
4. Is raised when task data violates business rules

#### Scenario: Invalid task data

**Given** a task creation attempt with empty task name  
**When** the validation rules are applied  
**Then** a `TaskValidationError` SHALL be raised  
**And** the exception message SHALL describe the validation failure  
**And** the exception MAY include the field name that failed

---

### Requirement: Invalid State Transition Exception

**ID**: `task-domain-exceptions-state-transition`  
**Priority**: Medium  
**Type**: Functional

The task domain SHALL provide an `InvalidStateTransitionError` exception that:
1. Inherits from `TaskDomainError`
2. Includes the `task_id` of the task being transitioned
3. Includes the `from_status` (current status)
4. Includes the `to_status` (attempted new status)
5. Is raised when attempting invalid state transitions

**Note**: This exception is prepared for User Story 4 (state machine validation) but is included here to establish the complete exception hierarchy.

#### Scenario: Invalid status transition

**Given** a task with status `completed`  
**When** attempting to transition to status `cancelled`  
**Then** an `InvalidStateTransitionError` SHALL be raised  
**And** the exception SHALL include `task_id`, `from_status = completed`, `to_status = cancelled`  
**And** the exception message SHALL indicate the invalid transition

---

### Requirement: Exception Context Preservation

**ID**: `task-domain-exceptions-context`  
**Priority**: High  
**Type**: Functional

All domain exceptions SHALL preserve context data as exception attributes (not just in the message), SHALL support both positional and keyword argument construction, SHALL generate default messages automatically from context, and SHALL allow custom messages to be provided.

#### Scenario: Exception attributes accessible

**Given** a `TaskNotFoundError` raised with `task_id = abc-123`  
**When** the exception is caught  
**Then** `exception.task_id` SHALL equal `abc-123`  
**And** the exception can be logged or inspected programmatically

#### Scenario: Custom error messages

**Given** raising a `TaskValidationError` with a custom message  
**When** the exception is constructed  
**Then** the custom message SHALL be preserved  
**And** the exception SHALL still be an instance of `TaskValidationError`

---

### Requirement: Exception Module Organization

**ID**: `task-domain-exceptions-organization`  
**Priority**: Medium  
**Type**: Non-Functional

The exception hierarchy SHALL be defined in `packages/tasky-tasks/src/tasky_tasks/exceptions.py`, SHALL be exported from `tasky_tasks.__init__` for external use, SHALL include docstrings explaining when each exception is raised, and SHALL follow Python exception naming conventions (suffix with `Error`).

#### Scenario: Importing exceptions

**Given** an external package needs to handle task domain errors  
**When** importing from `tasky_tasks`  
**Then** all exception classes SHALL be importable from the package root  
**And** IDEs SHALL provide autocomplete for exception names

---

### Requirement: Exception Serialization

**ID**: `task-domain-exceptions-serialization`  
**Priority**: Low  
**Type**: Non-Functional

Domain exceptions SHALL support string representation via `__str__` with human-readable messages, SHALL support `repr()` showing exception type and context attributes, SHALL be compatible with Python's traceback system, and SHALL preserve context through exception chaining.

#### Scenario: Exception string representation

**Given** a `TaskNotFoundError` with `task_id = uuid-value`  
**When** the exception is converted to string  
**Then** the string SHALL include a human-readable message  
**And** the message SHALL reference the task_id

#### Scenario: Exception debugging

**Given** an exception raised during development  
**When** inspecting the exception in a debugger or REPL  
**Then** `repr(exception)` SHALL show the exception type and key context  
**And** developers can identify the error source quickly

