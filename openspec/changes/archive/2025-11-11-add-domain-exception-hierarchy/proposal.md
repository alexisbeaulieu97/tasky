# Proposal: Domain Exception Hierarchy

**Status**: Draft  
**Created**: 2025-11-11  
**Change ID**: `add-domain-exception-hierarchy`

## Summary

Introduce a structured exception hierarchy in the task domain to enable precise error handling, provide clear user feedback, and separate domain concerns from infrastructure failures.

## Why

Currently, the codebase lacks domain-specific exceptions, leading to several issues:

1. **Poor error discrimination**: Cannot distinguish between "task not found" vs "validation error" vs "state transition error"
2. **Generic error messages**: Users see Python exceptions instead of actionable feedback
3. **Mixing concerns**: Domain logic cannot signal business rule violations without using generic exceptions
4. **Testing difficulty**: Tests cannot verify specific failure scenarios without catching broad exception types
5. **CLI complexity**: Presentation layer cannot provide targeted error handling and recovery strategies

The domain exception hierarchy separates:
- **Domain violations**: Business rule failures (not found, invalid transitions, validation)
- **Infrastructure failures**: Storage errors (I/O, serialization) 
- **Presentation concerns**: User-facing messages and exit codes

This enables the service layer to clearly communicate why an operation failed, allowing the CLI to provide contextual, actionable error messages.

## What Changes

- Create `packages/tasky-tasks/src/tasky_tasks/exceptions.py` with domain exception hierarchy
- Define `TaskDomainError`, `TaskNotFoundError`, `TaskValidationError`, `InvalidStateTransitionError`
- Update `packages/tasky-tasks/src/tasky_tasks/__init__.py` to export exception classes
- Modify `TaskService.get_task()` to raise `TaskNotFoundError` instead of returning `None`
- Modify `TaskService.delete_task()` to raise `TaskNotFoundError` for non-existent tasks
- Add exception handling to all CLI task commands with user-friendly messages
- Implement exit code strategy: 1 for domain errors, 3 for storage errors
- Add comprehensive unit tests for exceptions in `packages/tasky-tasks/tests/test_exceptions.py`
- Add service exception tests in `packages/tasky-tasks/tests/test_service_exceptions.py`
- Add CLI error handling tests in `packages/tasky-cli/tests/test_error_handling.py`

## Goals

1. **Domain Exception Types**: Create `TaskDomainError` base with specific subtypes for common scenarios
2. **Rich Context**: Include relevant data (task_id, status, etc.) in exceptions for debugging and logging
3. **Service Integration**: Update `TaskService` methods to raise appropriate domain exceptions
4. **CLI Error Handling**: Implement targeted error handlers with user-friendly messages
5. **Clear Propagation**: Document error flow from repository → service → CLI

## Non-Goals

- Generic application-wide exception handling middleware (future)
- Retry logic or error recovery strategies (future)
- Logging integration (separate logging system change)
- HTTP status code mapping (no web API yet)

## Affected Capabilities

### New Capabilities

1. **`task-domain-exceptions`**: Domain exception hierarchy for task operations
2. **`task-error-handling`**: Service layer integration with domain exceptions
3. **`cli-error-presentation`**: CLI error handlers with user-friendly messages

### Modified Capabilities

None (no existing specs to modify)

## Impact

- **Affected specs**: 
  - `task-domain-exceptions` (new capability)
  - `task-error-handling` (new capability)
  - `cli-error-presentation` (new capability)
- **Affected code**:
  - `packages/tasky-tasks/src/tasky_tasks/exceptions.py` (new file)
  - `packages/tasky-tasks/src/tasky_tasks/__init__.py` (modify exports)
  - `packages/tasky-tasks/src/tasky_tasks/service.py` (modify exception behavior)
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` (add error handling)
  - `packages/tasky-tasks/tests/` (new test files)
  - `packages/tasky-cli/tests/` (new test files)
- **Backward compatibility**: Compatible - pure addition, existing code continues to work
- **Dependencies**: None

## Design Decisions

### Exception Hierarchy Structure

```python
TaskDomainError (base)
├── TaskNotFoundError
├── TaskValidationError
└── InvalidStateTransitionError (prepared for future state machine)
```

**Rationale**: 
- Flat hierarchy keeps it simple and extensible
- Each exception type maps to a distinct user scenario
- Base class allows catching all domain errors if needed
- Prepared for state transition validation (User Story 4)

### Error Propagation Strategy

```
Repository Layer → Service Layer → CLI Layer
   (Storage)      (Domain + map)   (Present)
```

1. **Repository**: Raises `StorageDataError` for I/O/serialization failures
2. **Service**: 
   - Catches storage errors, may re-raise or wrap
   - Raises domain exceptions for business violations
3. **CLI**: Catches all, formats messages, exits with appropriate codes

**Rationale**:
- Clear separation between infrastructure and domain concerns
- Service layer acts as translation boundary
- CLI remains thin, focused on presentation

### Context Data in Exceptions

Exceptions include relevant identifiers and state for debugging:
- `TaskNotFoundError(task_id=...)`
- `InvalidStateTransitionError(task_id=..., from_status=..., to_status=...)`

**Rationale**:
- Enables detailed logging (future logging integration)
- Provides context for error messages without string parsing
- Supports structured error responses (future API work)

## Dependencies

- Requires: None (independent change)
- Blocks: None
- Enables: User Story 4 (state machine validation)

## Migration Strategy

### Phase 1: Foundation
1. Create `tasky-tasks/src/tasky_tasks/exceptions.py`
2. Define exception hierarchy with context attributes
3. Add comprehensive unit tests

### Phase 2: Service Integration
1. Update `TaskService.get_task()` to raise `TaskNotFoundError`
2. Update `TaskService.delete_task()` to raise `TaskNotFoundError` when appropriate
3. Add service-level tests verifying exception behavior

### Phase 3: CLI Integration
1. Add error handlers to task commands
2. Map exceptions to user-friendly messages
3. Add CLI integration tests for error scenarios

## Success Criteria

1. ✅ All domain exceptions include relevant context (task_id, status, etc.)
2. ✅ Service methods raise appropriate domain exceptions for business violations
3. ✅ CLI displays user-friendly, actionable error messages
4. ✅ Tests can verify specific failure scenarios using exception types
5. ✅ Error propagation follows documented repository → service → CLI flow
6. ✅ No generic `Exception` raises in service or CLI layers

## Testing Strategy

- **Unit tests**: Exception construction, context preservation
- **Service tests**: Verify correct exceptions raised for each scenario
- **CLI tests**: Validate error message formatting and exit codes
- **Integration tests**: End-to-end error handling (storage → CLI)

## Backward Compatibility

Compatible - this is a pure addition. Existing code continues to work, but new operations will use structured exceptions.

## Related Changes

- **Depends on**: None
- **Enables**: `add-task-state-machine` (User Story 4)
- **Related**: `add-configurable-storage-backends` (error handling for config issues)
