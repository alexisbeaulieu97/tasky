# Proposal: Task State Transition Validation

**Status**: Draft  
**Created**: 2025-11-11  
**Change ID**: `add-task-state-transitions`

## Summary

Implement a state machine for task status transitions with validation rules to ensure data integrity, enforce proper workflows, and prevent invalid state changes. Tasks will only be allowed to transition between valid states, with explicit service methods for each transition type.

## Why

Currently, task status can be changed arbitrarily without validation, leading to potential issues:

1. **No workflow enforcement**: Tasks could theoretically transition from any state to any other state without validation
2. **Unclear transition semantics**: Direct status assignment (`task.status = TaskStatus.COMPLETED`) doesn't express intent
3. **Missing business rules**: No validation that certain transitions are allowed while others are forbidden
4. **Poor auditability**: Can't distinguish between completing a task vs reopening vs canceling without examining status changes
5. **Difficult extension**: Adding new statuses or transition rules requires hunting through code

A proper state machine provides:
- **Explicit transitions**: Clear methods (`complete_task()`, `cancel_task()`, `reopen_task()`) express intent
- **Validation rules**: Enforce which transitions are allowed (e.g., can't cancel a completed task)
- **Business logic clarity**: State transition rules are centralized and testable
- **Better error messages**: Can provide specific feedback on why a transition failed

## What Changes

- Add `TASK_TRANSITIONS` dictionary to `TaskModel` defining valid state transitions
- Add state transition methods to `TaskModel`: `transition_to(status)` with validation
- Add convenience methods to `TaskModel`: `complete()`, `cancel()`, `reopen()`
- Add `InvalidStateTransitionError` exception (depends on `add-domain-exception-hierarchy`)
- Add service methods to `TaskService`: `complete_task()`, `cancel_task()`, `reopen_task()`
- Update service methods to call `task.mark_updated()` on state changes (depends on `add-automatic-timestamps`)
- Add CLI commands: `tasky task complete <id>`, `tasky task cancel <id>`, `tasky task reopen <id>`
- Add CLI error handling for `InvalidStateTransitionError` with user-friendly messages
- Add comprehensive tests for state transitions in `packages/tasky-tasks/tests/test_state_machine.py`
- Update service tests in `packages/tasky-tasks/tests/test_service.py` to cover new methods
- Add CLI command tests in `packages/tasky-cli/tests/test_task_commands.py`

## Goals

1. **Valid Transitions Only**: The system SHALL enforce allowed transitions: `pending → completed|cancelled`, `completed|cancelled → pending`
2. **Explicit Intent**: Service methods SHALL clearly express business operations (`complete_task` vs raw status change)
3. **Clear Validation**: The system SHALL raise `InvalidStateTransitionError` with context when invalid transitions are attempted
4. **Timestamp Integration**: State transitions SHALL automatically update `updated_at` via `mark_updated()`
5. **User-Friendly CLI**: Commands SHALL match user mental model (`complete`, `cancel`, `reopen`)
6. **Extensible**: The system SHALL make it easy to add new statuses and transition rules in centralized location

## Non-Goals

- Complex workflow states (e.g., "in progress", "blocked", "waiting")
- Task dependencies or prerequisite validation
- Transition history or audit log (future consideration)
- Permissions or authorization for state changes
- Scheduled or automated state transitions
- Reversible transitions beyond simple reopen (e.g., undo complete)
- State-specific data validation (e.g., requiring completion notes)

## Impact

### On Existing Features

- **Task Model**: Adds transition validation, but doesn't break direct status assignment during creation
- **Task Service**: Extends with new methods, existing methods unchanged
- **CLI**: Adds new commands, existing commands unaffected
- **Storage**: No changes required, state transitions use existing `save_task()` mechanism

### On Dependencies

**Requires**:
- `add-domain-exception-hierarchy` → Needs `InvalidStateTransitionError`
- `add-automatic-timestamps` → Should call `mark_updated()` on transitions

**Blocks**: None

**Enables**:
- Future workflow enhancements (task dependencies, scheduled transitions)
- Audit logging of state changes
- Permission-based transition rules

### On Users

- **New CLI commands**: Users gain explicit lifecycle commands (`complete`, `cancel`, `reopen`)
- **Better errors**: Clear messages when attempting invalid transitions
- **Backward compatible**: Existing task data continues to work
- **Migration**: No migration needed, existing task statuses remain valid

### Breaking Changes

None. This is purely additive:
- New methods added to existing classes
- New CLI commands added alongside existing ones
- Existing task creation and status setting continues to work
- State validation only applies to new transition methods

## Success Criteria

1. **Transition Enforcement**: The system SHALL raise `InvalidStateTransitionError` for invalid transitions (e.g., `cancelled → completed`)
2. **Method Availability**: The system SHALL provide `complete_task()`, `cancel_task()`, `reopen_task()` methods that work correctly
3. **Timestamp Updates**: All state transitions SHALL update `updated_at` timestamp
4. **CLI Commands**: The CLI SHALL execute `tasky task complete/cancel/reopen <id>` successfully
5. **Error Messages**: The system SHALL show clear, actionable error messages for invalid transition attempts
6. **Test Coverage**: The implementation SHALL achieve ≥90% coverage for state machine logic and transition validation
7. **Documentation**: The implementation SHALL include state diagram in code comments and/or docs

## Alternatives Considered

### 1. No State Machine (Status Quo)
**Rejected**: Allows invalid transitions, lacks business logic enforcement, harder to extend

### 2. External State Machine Library (e.g., python-statemachine)
**Rejected**: Adds dependency for simple state logic, overkill for current needs, harder to customize

### 3. Immutable State Pattern
**Rejected**: Would require creating new task objects on transitions, breaks repository pattern, complicates identity tracking

### 4. Event-Based Transitions
**Rejected**: Premature complexity, hooks system not yet implemented, adds async concerns

## Dependencies

### Upstream (Blocks This)
- **add-domain-exception-hierarchy**: Provides `InvalidStateTransitionError`
- **add-automatic-timestamps**: Provides `TaskModel.mark_updated()` method

### Downstream (This Blocks)
None currently, but future features could build on state machine:
- Task workflow automation
- Transition-based hooks/events
- Advanced reporting on task lifecycles

## References

- VISION.md: User Story 4 - Task State Transition Validation
- Domain-Driven Design: Aggregate state consistency
- State Machine Pattern: GoF Design Patterns
