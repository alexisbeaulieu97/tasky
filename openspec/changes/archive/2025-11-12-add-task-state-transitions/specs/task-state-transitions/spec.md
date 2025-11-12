# Spec: Task State Transitions

**Capability ID**: `task-state-transitions`  
**Status**: New Capability  
**Related Changes**: `add-task-state-transitions`

---

## ADDED Requirements

### Requirement: System MUST Enforce Valid State Transitions
**ID**: `REQ-TST-001`  
**Priority**: Must Have

The system MUST enforce valid state transitions for tasks according to defined business rules.

#### Scenario: Complete a pending task
**Given** a task exists with status "pending"  
**When** the user executes `complete_task(task_id)`  
**Then** the task status transitions to "completed"  
**And** the task's `updated_at` timestamp is updated to current UTC time

#### Scenario: Cancel a pending task
**Given** a task exists with status "pending"  
**When** the user executes `cancel_task(task_id)`  
**Then** the task status transitions to "cancelled"  
**And** the task's `updated_at` timestamp is updated to current UTC time

#### Scenario: Reopen a completed task
**Given** a task exists with status "completed"  
**When** the user executes `reopen_task(task_id)`  
**Then** the task status transitions to "pending"  
**And** the task's `updated_at` timestamp is updated to current UTC time

#### Scenario: Reopen a cancelled task
**Given** a task exists with status "cancelled"  
**When** the user executes `reopen_task(task_id)`  
**Then** the task status transitions to "pending"  
**And** the task's `updated_at` timestamp is updated to current UTC time

---

### Requirement: System MUST Prevent Invalid State Transitions
**ID**: `REQ-TST-002`  
**Priority**: Must Have

The system MUST prevent invalid state transitions and provide clear error feedback.

#### Scenario: Attempt to cancel a completed task
**Given** a task exists with status "completed"  
**When** the user executes `cancel_task(task_id)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the error includes current status "completed"  
**And** the error includes target status "cancelled"  
**And** the task status remains "completed"

#### Scenario: Attempt to complete a cancelled task
**Given** a task exists with status "cancelled"  
**When** the user executes `complete_task(task_id)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the error includes current status "cancelled"  
**And** the error includes target status "completed"  
**And** the task status remains "cancelled"

#### Scenario: Attempt to complete an already completed task
**Given** a task exists with status "completed"  
**When** the user executes `complete_task(task_id)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the error includes current status "completed"  
**And** the error includes target status "completed"  
**And** the task status remains "completed"

#### Scenario: Attempt to cancel an already cancelled task
**Given** a task exists with status "cancelled"  
**When** the user executes `cancel_task(task_id)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the error includes current status "cancelled"  
**And** the error includes target status "cancelled"  
**And** the task status remains "cancelled"

#### Scenario: Attempt to reopen a pending task
**Given** a task exists with status "pending"  
**When** the user executes `reopen_task(task_id)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the error includes current status "pending"  
**And** the error includes target status "pending"  
**And** the task status remains "pending"

---

### Requirement: TaskModel MUST Provide State Transition Methods
**ID**: `REQ-TST-003`  
**Priority**: Must Have

The `TaskModel` MUST provide methods for state transitions with built-in validation.

#### Scenario: TaskModel provides transition_to method
**Given** a `TaskModel` instance with status "pending"  
**When** calling `task.transition_to(TaskStatus.COMPLETED)`  
**Then** the task status changes to "completed"  
**And** the `updated_at` timestamp is updated via `mark_updated()`  
**And** no exception is raised

#### Scenario: TaskModel validates transitions in transition_to
**Given** a `TaskModel` instance with status "completed"  
**When** calling `task.transition_to(TaskStatus.CANCELLED)`  
**Then** an `InvalidStateTransitionError` is raised  
**And** the task status remains "completed"  
**And** the `updated_at` timestamp is not modified

#### Scenario: TaskModel provides convenience complete method
**Given** a `TaskModel` instance with status "pending"  
**When** calling `task.complete()`  
**Then** the task status changes to "completed"  
**And** the method internally calls `transition_to(TaskStatus.COMPLETED)`

#### Scenario: TaskModel provides convenience cancel method
**Given** a `TaskModel` instance with status "pending"  
**When** calling `task.cancel()`  
**Then** the task status changes to "cancelled"  
**And** the method internally calls `transition_to(TaskStatus.CANCELLED)`

#### Scenario: TaskModel provides convenience reopen method
**Given** a `TaskModel` instance with status "completed"  
**When** calling `task.reopen()`  
**Then** the task status changes to "pending"  
**And** the method internally calls `transition_to(TaskStatus.PENDING)`

---

### Requirement: System SHALL Define State Transition Rules Centrally
**ID**: `REQ-TST-004`  
**Priority**: Must Have

The system MUST define state transition rules in a centralized, maintainable structure.

#### Scenario: Transition rules defined in TASK_TRANSITIONS constant
**Given** the `tasky_tasks.models` module  
**When** accessing the `TASK_TRANSITIONS` constant  
**Then** it is a dictionary mapping `TaskStatus` to sets of allowed target statuses  
**And** `PENDING` maps to `{COMPLETED, CANCELLED}`  
**And** `COMPLETED` maps to `{PENDING}`  
**And** `CANCELLED` maps to `{PENDING}`

#### Scenario: Transition validation uses TASK_TRANSITIONS
**Given** a task with any status  
**When** `transition_to(target_status)` is called  
**Then** the validation checks if `target_status in TASK_TRANSITIONS[current_status]`  
**And** raises `InvalidStateTransitionError` if not found  
**And** proceeds with transition if found

---

### Requirement: TaskService MUST Provide State Transition Operations
**ID**: `REQ-TST-005`  
**Priority**: Must Have

The `TaskService` MUST provide business operations for state transitions that orchestrate fetching, validation, and persistence.

#### Scenario: Service provides complete_task method
**Given** a `TaskService` instance  
**When** calling `service.complete_task(task_id)`  
**Then** the service fetches the task via `repository.get_task(task_id)`  
**And** raises `TaskNotFoundError` if task is None  
**And** calls `task.complete()` on the fetched task  
**And** saves the task via `repository.save_task(task)`  
**And** returns the updated task

#### Scenario: Service provides cancel_task method
**Given** a `TaskService` instance  
**When** calling `service.cancel_task(task_id)`  
**Then** the service fetches the task via `repository.get_task(task_id)`  
**And** raises `TaskNotFoundError` if task is None  
**And** calls `task.cancel()` on the fetched task  
**And** saves the task via `repository.save_task(task)`  
**And** returns the updated task

#### Scenario: Service provides reopen_task method
**Given** a `TaskService` instance  
**When** calling `service.reopen_task(task_id)`  
**Then** the service fetches the task via `repository.get_task(task_id)`  
**And** raises `TaskNotFoundError` if task is None  
**And** calls `task.reopen()` on the fetched task  
**And** saves the task via `repository.save_task(task)`  
**And** returns the updated task

#### Scenario: Service propagates InvalidStateTransitionError
**Given** a task with status "completed"  
**When** calling `service.cancel_task(task_id)`  
**Then** the service calls `task.cancel()`  
**And** `task.cancel()` raises `InvalidStateTransitionError`  
**And** the service does not catch this exception  
**And** the exception propagates to the caller

---

### Requirement: CLI MUST Provide User-Friendly State Transition Commands
**ID**: `REQ-TST-006`  
**Priority**: Must Have

The CLI MUST provide user-friendly commands for task state transitions with clear error messages.

#### Scenario: CLI complete command marks task as completed
**Given** a pending task with ID "abc-123"  
**When** the user runs `tasky task complete abc-123`  
**Then** the CLI calls `task_service.complete_task(uuid)`  
**And** displays a success message including the task name  
**And** exits with code 0

#### Scenario: CLI cancel command marks task as cancelled
**Given** a pending task with ID "abc-123"  
**When** the user runs `tasky task cancel abc-123`  
**Then** the CLI calls `task_service.cancel_task(uuid)`  
**And** displays a success message including the task name  
**And** exits with code 0

#### Scenario: CLI reopen command restores task to pending
**Given** a completed task with ID "abc-123"  
**When** the user runs `tasky task reopen abc-123`  
**Then** the CLI calls `task_service.reopen_task(uuid)`  
**And** displays a success message including the task name  
**And** exits with code 0

#### Scenario: CLI handles TaskNotFoundError gracefully
**Given** no task exists with ID "abc-123"  
**When** the user runs `tasky task complete abc-123`  
**Then** the CLI catches `TaskNotFoundError`  
**And** displays error message "Task not found: abc-123"  
**And** exits with code 1

#### Scenario: CLI handles InvalidStateTransitionError with guidance
**Given** a completed task with ID "abc-123"  
**When** the user runs `tasky task cancel abc-123`  
**Then** the CLI catches `InvalidStateTransitionError`  
**And** displays error message explaining the current state  
**And** suggests using `reopen` command first  
**And** exits with code 1

#### Scenario: CLI handles invalid UUID format
**Given** the user provides an invalid UUID "not-a-uuid"  
**When** the user runs `tasky task complete not-a-uuid`  
**Then** the CLI catches `ValueError` during UUID parsing  
**And** displays error message about invalid UUID format  
**And** exits with code 1

---

## Dependencies

### Upstream Dependencies (Required Before This)
- **add-domain-exception-hierarchy**: Provides `InvalidStateTransitionError` exception class
- **add-automatic-timestamps**: Provides `TaskModel.mark_updated()` method for timestamp updates

### Downstream Dependencies (Enabled By This)
- None currently, but future capabilities could build on this:
  - Task workflow automation
  - Transition-based event hooks
  - State-dependent permissions

---

## Acceptance Criteria

1. **Valid Transitions Work**: All allowed transitions (pending→completed, pending→cancelled, completed/cancelled→pending) succeed
2. **Invalid Transitions Blocked**: All forbidden transitions raise `InvalidStateTransitionError`
3. **Timestamp Updates**: All successful transitions update `updated_at` timestamp
4. **Service Integration**: Service methods correctly orchestrate fetch, transition, persist
5. **CLI Commands Available**: `complete`, `cancel`, `reopen` commands work end-to-end
6. **Error Handling**: CLI provides clear, actionable error messages for all failure cases
7. **Test Coverage**: ≥90% coverage for state machine and transition logic
8. **No Breaking Changes**: Existing code and data continue to work without modification

---

## Out of Scope

- Complex workflow states (in-progress, blocked, waiting)
- Task dependencies or prerequisites
- Transition history/audit log
- Permissions/authorization for transitions
- Scheduled or automated transitions
- State-specific validation rules
- Reversible transitions beyond simple reopen
