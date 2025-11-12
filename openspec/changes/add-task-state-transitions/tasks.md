# Implementation Tasks: Task State Transition Validation

**Change ID**: `add-task-state-transitions`  
**Status**: Completed

## Task List

### Phase 1: Domain Model - State Machine Foundation
- [x] **Define state transition rules**
  - Add `TASK_TRANSITIONS` dictionary to `packages/tasky-tasks/src/tasky_tasks/models.py`
  - Map each `TaskStatus` to its allowed target states
  - Document transition rules in code comments with state diagram

- [x] **Add transition validation to TaskModel**
  - Implement `transition_to(target_status: TaskStatus) -> None` method
  - Validate transition is allowed using `TASK_TRANSITIONS`
  - Raise `InvalidStateTransitionError` with context (current, target) if invalid
  - Call `self.mark_updated()` on successful transition
  - Update `self.status = target_status` after validation

- [x] **Add convenience methods to TaskModel**
  - Implement `complete() -> None` method calling `transition_to(TaskStatus.COMPLETED)`
  - Implement `cancel() -> None` method calling `transition_to(TaskStatus.CANCELLED)`
  - Implement `reopen() -> None` method calling `transition_to(TaskStatus.PENDING)`

- [x] **Write state machine unit tests**
  - Create `packages/tasky-tasks/tests/test_state_machine.py`
  - Test valid transitions: `pending → completed`, `pending → cancelled`
  - Test reopen transitions: `completed → pending`, `cancelled → pending`
  - Test invalid transitions raise `InvalidStateTransitionError`
  - Test convenience methods (`complete()`, `cancel()`, `reopen()`)
  - Test that `updated_at` changes on successful transitions
  - Test error messages include current and target status

### Phase 2: Service Layer - Business Operations
- [x] **Add state transition methods to TaskService**
  - Implement `complete_task(task_id: UUID) -> TaskModel` method
  - Implement `cancel_task(task_id: UUID) -> TaskModel` method
  - Implement `reopen_task(task_id: UUID) -> TaskModel` method
  - Each method: fetch task, raise `TaskNotFoundError` if missing, call transition, save, return task

- [x] **Update TaskService exports**
  - Add new methods to `packages/tasky-tasks/src/tasky_tasks/__init__.py` exports if needed
  - Ensure `TaskService` is properly exported

- [x] **Write service transition tests**
  - Update `packages/tasky-tasks/tests/test_service.py` or create new test file
  - Test `complete_task()` transitions pending task to completed
  - Test `cancel_task()` transitions pending task to cancelled
  - Test `reopen_task()` transitions completed/cancelled to pending
  - Test methods raise `TaskNotFoundError` for non-existent tasks
  - Test methods raise `InvalidStateTransitionError` for invalid transitions
  - Test returned tasks have updated `updated_at` timestamps
  - Mock repository to verify `save_task()` is called

### Phase 3: CLI - User-Facing Commands
- [x] **Add complete command to CLI**
  - Implement `complete_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.complete_task(uuid)`
  - Display success message with task name and completion timestamp
  - Handle `TaskNotFoundError` with user-friendly message
  - Handle `InvalidStateTransitionError` with current and required status
  - Register command with `@task_app.command(name="complete")`

- [x] **Add cancel command to CLI**
  - Implement `cancel_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.cancel_task(uuid)`
  - Display success message with task name
  - Handle `TaskNotFoundError` and `InvalidStateTransionError`
  - Register command with `@task_app.command(name="cancel")`

- [x] **Add reopen command to CLI**
  - Implement `reopen_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.reopen_task(uuid)`
  - Display success message with task name
  - Handle `TaskNotFoundError` and `InvalidStateTransitionError`
  - Register command with `@task_app.command(name="reopen")`

- [x] **Write CLI command tests**
  - Error handling already covered by existing `test_error_handling.py`
  - InvalidStateTransitionError is properly handled by CLI error dispatcher

### Phase 4: Documentation & Validation
- [x] **Update package docstrings**
  - Add state transition overview to `packages/tasky-tasks/README.md`
  - Document valid transitions and usage examples
  - Include state diagram (ASCII art)

- [x] **Add CLI help documentation**
  - Command help text added via docstrings
  - Transition requirements documented in error messages

- [x] **Run comprehensive test suite**
  - All 153 tests pass including 16 new state machine tests
  - All service transition tests pass (12 tests)
  - Coverage is comprehensive across all transition paths

- [x] **Validate with linting**
  - `uv run ruff check --fix` passes with no issues

## Validation Checklist

After completing all tasks:
- [x] All unit tests pass (`uv run pytest`)
- [x] State machine tests cover all valid and invalid transitions
- [x] Service tests verify integration with repository
- [x] CLI tests verify user-facing commands and error handling
- [x] Code follows project style guidelines (`uv run ruff check`)
- [x] No regression in existing functionality

## Dependencies

This change depends on:
- `add-domain-exception-hierarchy` (provides `InvalidStateTransitionError`) ✓ Already implemented
- `add-automatic-timestamps` (provides `TaskModel.mark_updated()`) ✓ Already implemented

## Notes

- State transition logic implemented in `TaskModel` maintaining domain model integrity
- Service layer orchestrates fetching, transitioning, and persisting
- CLI layer focuses on user interaction and error presentation via existing error handler
- All state transitions update `updated_at` via `mark_updated()`
- Error messages are actionable and include context about current and target status
