# Tasky Tasks

Domain models, services, and business logic for task management in Tasky.

## Overview

The `tasky-tasks` package provides the core domain layer for task management, including:

- **Task Models**: Pydantic models representing tasks with automatic timestamp management
- **Task Service**: Orchestration layer for task operations including state transitions
- **State Machine**: Validated status transitions with business rule enforcement
- **Domain Exceptions**: Specialized exceptions for task-related errors

## Task State Machine

Tasks follow a finite state machine with validated transitions:

```
    PENDING ────┐
       ↑        │
       │        ├─→ COMPLETED
       │        │
    reopen      │
       │        └─→ CANCELLED
       ↓
  COMPLETED/CANCELLED
```

### Valid Transitions

- **PENDING → COMPLETED**: Mark a task as done
- **PENDING → CANCELLED**: Cancel a pending task
- **COMPLETED → PENDING**: Reopen a completed task
- **CANCELLED → PENDING**: Reopen a cancelled task

### Invalid Transitions

Attempts to perform invalid transitions (e.g., `COMPLETED → CANCELLED`) raise `InvalidStateTransitionError`.

## Usage

### Creating and Transitioning Tasks

```python
from tasky_tasks.models import TaskModel, TaskStatus
from tasky_tasks.service import TaskService
from tasky_tasks.exceptions import InvalidStateTransitionError

# Create a task (defaults to PENDING status)
task = TaskModel(name="Write documentation", details="Document the state machine")

# Transition using convenience methods
task.complete()  # PENDING → COMPLETED
task.reopen()    # COMPLETED → PENDING
task.cancel()    # PENDING → CANCELLED

# Or use the generic transition_to method
task.transition_to(TaskStatus.PENDING)

# Invalid transitions raise errors
try:
    completed_task.cancel()  # COMPLETED → CANCELLED is invalid
except InvalidStateTransitionError as e:
    print(f"Cannot transition from {e.from_status} to {e.to_status}")
```

### Using the Service Layer

```python
from uuid import UUID
from tasky_tasks.service import TaskService

# Service methods handle fetch → transition → save
service = TaskService(repository)

# State transition operations
task = service.complete_task(task_id)  # Marks task as completed
task = service.cancel_task(task_id)    # Marks task as cancelled
task = service.reopen_task(task_id)    # Reopens a completed/cancelled task

# Service methods raise TaskNotFoundError if task doesn't exist
# and InvalidStateTransitionError for invalid transitions
```

## Automatic Timestamps

Tasks automatically track creation and update times:

- `created_at`: Set once at task creation (UTC)
- `updated_at`: Refreshed automatically on state transitions via `mark_updated()`

```python
task = TaskModel(name="Example", details="Details")
print(f"Created: {task.created_at}")

task.complete()
print(f"Updated: {task.updated_at}")  # Newer than created_at
```

## Domain Exceptions

The package defines a hierarchy of domain exceptions:

- `TaskDomainError`: Base exception for all task-related errors
- `TaskNotFoundError`: Raised when a task doesn't exist
- `TaskValidationError`: Raised for validation failures
- `InvalidStateTransitionError`: Raised for invalid state transitions

All exceptions include structured context for debugging and user-friendly error messages.

## Architecture

This package follows clean architecture principles:

- **Models** (`models.py`): Pure domain models with business logic
- **Service** (`service.py`): Orchestration layer, handles persistence
- **Ports** (`ports.py`): Repository protocols (implemented by storage layer)
- **Exceptions** (`exceptions.py`): Domain-specific error types

The package has no dependencies on infrastructure (storage, CLI, etc.) - those layers depend on this package.
