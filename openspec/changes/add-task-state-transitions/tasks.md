# Implementation Tasks: Task State Transition Validation

**Change ID**: `add-task-state-transitions`  
**Status**: Not Started

## Task List

### Phase 1: Domain Model - State Machine Foundation
- [ ] **Define state transition rules**
  - Add `TASK_TRANSITIONS` dictionary to `packages/tasky-tasks/src/tasky_tasks/models.py`
  - Map each `TaskStatus` to its allowed target states
  - Document transition rules in code comments with state diagram

- [ ] **Add transition validation to TaskModel**
  - Implement `transition_to(target_status: TaskStatus) -> None` method
  - Validate transition is allowed using `TASK_TRANSITIONS`
  - Raise `InvalidStateTransitionError` with context (current, target) if invalid
  - Call `self.mark_updated()` on successful transition
  - Update `self.status = target_status` after validation

- [ ] **Add convenience methods to TaskModel**
  - Implement `complete() -> None` method calling `transition_to(TaskStatus.COMPLETED)`
  - Implement `cancel() -> None` method calling `transition_to(TaskStatus.CANCELLED)`
  - Implement `reopen() -> None` method calling `transition_to(TaskStatus.PENDING)`

- [ ] **Write state machine unit tests**
  - Create `packages/tasky-tasks/tests/test_state_machine.py`
  - Test valid transitions: `pending → completed`, `pending → cancelled`
  - Test reopen transitions: `completed → pending`, `cancelled → pending`
  - Test invalid transitions raise `InvalidStateTransitionError`
  - Test convenience methods (`complete()`, `cancel()`, `reopen()`)
  - Test that `updated_at` changes on successful transitions
  - Test error messages include current and target status

### Phase 2: Service Layer - Business Operations
- [ ] **Add state transition methods to TaskService**
  - Implement `complete_task(task_id: UUID) -> TaskModel` method
  - Implement `cancel_task(task_id: UUID) -> TaskModel` method
  - Implement `reopen_task(task_id: UUID) -> TaskModel` method
  - Each method: fetch task, raise `TaskNotFoundError` if missing, call transition, save, return task

- [ ] **Update TaskService exports**
  - Add new methods to `packages/tasky-tasks/src/tasky_tasks/__init__.py` exports if needed
  - Ensure `TaskService` is properly exported

- [ ] **Write service transition tests**
  - Update `packages/tasky-tasks/tests/test_service.py` or create new test file
  - Test `complete_task()` transitions pending task to completed
  - Test `cancel_task()` transitions pending task to cancelled
  - Test `reopen_task()` transitions completed/cancelled to pending
  - Test methods raise `TaskNotFoundError` for non-existent tasks
  - Test methods raise `InvalidStateTransitionError` for invalid transitions
  - Test returned tasks have updated `updated_at` timestamps
  - Mock repository to verify `save_task()` is called

### Phase 3: CLI - User-Facing Commands
- [ ] **Add complete command to CLI**
  - Implement `complete_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.complete_task(uuid)`
  - Display success message with task name and completion timestamp
  - Handle `TaskNotFoundError` with user-friendly message
  - Handle `InvalidStateTransitionError` with current and required status
  - Register command with `@task_app.command(name="complete")`

- [ ] **Add cancel command to CLI**
  - Implement `cancel_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.cancel_task(uuid)`
  - Display success message with task name
  - Handle `TaskNotFoundError` and `InvalidStateTransionError`
  - Register command with `@task_app.command(name="cancel")`

- [ ] **Add reopen command to CLI**
  - Implement `reopen_command(task_id: str)` in `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Parse and validate task_id UUID
  - Call `task_service.reopen_task(uuid)`
  - Display success message with task name
  - Handle `TaskNotFoundError` and `InvalidStateTransitionError`
  - Register command with `@task_app.command(name="reopen")`

- [ ] **Write CLI command tests**
  - Create or update `packages/tasky-cli/tests/test_task_commands.py`
  - Test `complete` command with valid pending task
  - Test `cancel` command with valid pending task
  - Test `reopen` command with completed task
  - Test `reopen` command with cancelled task
  - Test commands with non-existent task_id show error
  - Test commands with invalid transition show status requirements
  - Test commands with invalid UUID format show parse error
  - Verify exit codes: 0 for success, 1 for domain errors

### Phase 4: Documentation & Validation
- [ ] **Update package docstrings**
  - Add state transition overview to `packages/tasky-tasks/README.md`
  - Document valid transitions and usage examples
  - Include state diagram (mermaid or ASCII art)

- [ ] **Add CLI help documentation**
  - Ensure command help text explains when each command can be used
  - Document valid transition paths in help strings

- [ ] **Run comprehensive test suite**
  - Execute `uv run pytest packages/tasky-tasks/tests/test_state_machine.py -v`
  - Execute `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
  - Execute `uv run pytest packages/tasky-cli/tests/test_task_commands.py -v`
  - Verify all tests pass
  - Check coverage meets ≥90% for state machine code

- [ ] **Validate with openspec**
  - Run `openspec validate add-task-state-transitions --strict`
  - Fix any validation errors
  - Ensure all spec deltas are correctly formatted

## Validation Checklist

After completing all tasks:
- [ ] All unit tests pass (`uv run pytest`)
- [ ] State machine tests cover all valid and invalid transitions
- [ ] Service tests verify integration with repository
- [ ] CLI tests verify user-facing commands and error handling
- [ ] Manual smoke test: `uv run tasky task create "Test" "Details"` → `complete` → `reopen` → `cancel`
- [ ] Code follows project style guidelines (`uv run ruff check`)
- [ ] No regression in existing functionality
- [ ] OpenSpec validation passes with `--strict` flag

## Dependencies

This change depends on:
- `add-domain-exception-hierarchy` (provides `InvalidStateTransitionError`)
- `add-automatic-timestamps` (provides `TaskModel.mark_updated()`)

Ensure these changes are implemented first or implemented in parallel with coordination.

## Notes

- Keep state transition logic in `TaskModel` to maintain domain model integrity
- Service layer orchestrates fetching, transitioning, and persisting
- CLI layer focuses on user interaction and error presentation
- All state transitions should update `updated_at` via `mark_updated()`
- Error messages should be actionable (e.g., "Task is already completed. Use 'reopen' to make it pending again.")
