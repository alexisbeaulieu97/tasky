# ADR-002: Error Handling Strategy - Domain vs Infrastructure Errors

## Status
Accepted

## Context
The system has three distinct layers with different error concerns:

1. **Domain layer** (`tasky-tasks`): Business rule violations (task not found, invalid state transitions)
2. **Infrastructure layer** (`tasky-storage`): I/O failures, data corruption, serialization errors
3. **Presentation layer** (`tasky-cli`): User input validation, command failures

Without a clear error strategy, the domain layer became coupled to infrastructure exceptions (e.g., importing `StorageDataError` from `tasky_storage`), violating clean architecture principles.

## Decision
We implement a **protocol-based error decoupling strategy**:

1. **Domain Layer** publishes a `StorageErrorProtocol` that describes the shape of storage errors without importing infrastructure code
2. **Service methods** catch exceptions matching the protocol and translate them to domain exceptions
3. **Infrastructure layer** implements the protocol by adding a marker attribute (`__is_storage_error__ = True`) to storage exceptions
4. **Protocol is runtime-checkable** using `@runtime_checkable` decorator for `isinstance()` checks

**Error Translation Flow:**
```
Repository (Storage Error) → Service Layer → Domain Exception
    ↓                              ↓                  ↓
StorageDataError          isinstance(exc, Protocol)  TaskValidationError
    ↓                              ↓                  ↓
__is_storage_error__=True    if match: translate    Re-raised to caller
```

**Implementation:**
```python
# Domain layer (tasky-tasks/protocols.py)
@runtime_checkable
class StorageErrorProtocol(Protocol):
    __is_storage_error__: bool
    def __str__(self) -> str: ...

# Service layer (tasky-tasks/service.py)
def get_task(self, task_id: UUID) -> TaskModel:
    try:
        task = self.repository.get_task(task_id)
    except Exception as exc:
        if isinstance(exc, StorageErrorProtocol):
            raise TaskValidationError(...) from exc
        raise  # Re-raise unexpected errors

# Infrastructure layer (tasky-storage/errors.py)
class StorageDataError(StorageError):
    __is_storage_error__ = True  # Implements protocol
```

## Consequences

### Positive
- **Zero coupling**: Domain layer never imports infrastructure packages
- **Clear boundaries**: Each layer has its own exception hierarchy
- **Protocol flexibility**: Any exception can implement the protocol by adding the marker
- **Preserves error chain**: Original exceptions preserved via `raise ... from exc`
- **Type-safe**: Pyright validates protocol conformance at type-check time

### Negative
- **Marker boilerplate**: Each storage error needs `__is_storage_error__ = True`
- **Runtime check overhead**: `isinstance()` checks add minimal overhead (acceptable)
- **Protocol complexity**: Contributors must understand structural typing

## Alternatives Considered

### Alternative 1: Direct Exception Imports
Import storage exceptions directly in the domain layer:
```python
from tasky_storage.errors import StorageDataError

def get_task(self, task_id):
    try:
        return self.repository.get_task(task_id)
    except StorageDataError as exc:
        raise TaskValidationError(...) from exc
```

**Rejected because:**
- Creates tight coupling between domain and infrastructure
- Violates clean architecture / hexagonal architecture principles
- Makes domain layer tests depend on infrastructure packages
- Harder to swap storage implementations

### Alternative 2: Base Exception Class in Shared Module
Create a shared exceptions module imported by both layers:
```python
# tasky-shared/exceptions.py
class StorageErrorBase(Exception): pass

# Both layers import this
```

**Rejected because:**
- Requires a new "shared" package, increasing complexity
- Still creates coupling (both layers depend on shared module)
- Doesn't solve the architectural layering problem

### Alternative 3: Catch All Exceptions
Catch `Exception` without type checking:
```python
try:
    task = self.repository.get_task(task_id)
except Exception as exc:
    raise TaskValidationError(...) from exc
```

**Rejected because:**
- Too broad: catches unexpected errors (KeyboardInterrupt, SystemExit, etc.)
- Masks programming errors that should propagate
- No way to distinguish storage errors from other failures

## References
- `packages/tasky-tasks/src/tasky_tasks/protocols.py` - Protocol definition
- `packages/tasky-tasks/src/tasky_tasks/service.py` - Protocol usage
- `packages/tasky-storage/src/tasky_storage/errors.py` - Protocol implementation
- Clean Architecture by Robert C. Martin (error translation across boundaries)
