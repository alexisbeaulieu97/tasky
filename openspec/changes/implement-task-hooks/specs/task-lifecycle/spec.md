## ADDED Requirements

### Requirement: Task Lifecycle Events

The system SHALL emit structured events when tasks undergo state transitions or important operations. Events SHALL include complete context (task snapshot, old/new values, timestamps) and be available for external handlers.

#### Scenario: Task creation emits event
- **WHEN** a task is created via service or CLI
- **THEN** a `TaskCreatedEvent` is emitted
- **AND** event includes task_id, name, details, status, timestamp
- **AND** all registered handlers receive the event

#### Scenario: Task update emits event with delta
- **WHEN** a task is updated (name, details, priority, due date)
- **THEN** a `TaskUpdatedEvent` is emitted
- **AND** event includes task_id, old values, new values, timestamp
- **AND** handlers can see what changed

#### Scenario: Task status transitions emit events
- **WHEN** a task transitions to completed, cancelled, or reopened
- **THEN** appropriate event is emitted (TaskCompletedEvent, TaskCancelledEvent, TaskReopenedEvent)
- **AND** event includes previous status, new status, timestamp
- **AND** handlers receive event immediately

#### TaskCancelledEvent Definition
- **Event name**: `task_cancelled`
- **Payload**:
  - `task_id: UUID` — ID of the cancelled task
  - `previous_status: str` — Status before cancellation (usually "pending" or "in_progress")
  - `timestamp: ISO8601 datetime` — When cancellation occurred
  - `task_snapshot: TaskModel` — Full task state before cancellation
  - `reason: str | None` — Optional cancellation reason provided by user
- **Example context**: User cancelled a task because requirements changed
- **Handler requirements**: Handlers should preserve cancellation metadata if forwarding to external systems

#### TaskReopenedEvent Definition
- **Event name**: `task_reopened`
- **Payload**:
  - `task_id: UUID` — ID of the reopened task
  - `previous_status: str` — Status before reopening (usually "completed" or "cancelled")
  - `new_status: str` — Status after reopening (usually "pending")
  - `timestamp: ISO8601 datetime` — When reopening occurred
  - `task_snapshot: TaskModel` — Full task state after reopening
- **Example context**: User reopened a completed task because it needs more work
- **Handler requirements**: Handlers may need to reverse previously applied completions (e.g., removing from "done" list in external systems)

#### Scenario: Task deletion emits event
- **WHEN** a task is deleted
- **THEN** a `TaskDeletedEvent` is emitted
- **AND** event includes the full task snapshot (before deletion)
- **AND** handlers can log/audit the deletion

#### Scenario: Bulk import emits summary event
- **WHEN** multiple tasks are imported
- **THEN** a `TasksImportedEvent` is emitted
- **AND** event includes count of imported, skipped, failed
- **AND** event includes import strategy used

### Requirement: Hook Handler Registration

Users SHALL be able to register custom handlers that execute when events occur. Handlers SHALL receive full event context and have access to the task state.

#### Scenario: Handler is registered for event type
- **WHEN** a user registers a handler for "task_created" events
- **THEN** handler is called whenever a task is created
- **AND** handler receives TaskCreatedEvent object
- **AND** handler can access task_id, name, details, timestamp

#### Scenario: Multiple handlers for same event
- **GIVEN** multiple handlers registered for "task_completed"
- **WHEN** a task is completed
- **THEN** all handlers are called in registration order
- **AND** if one handler fails, others still execute
- **AND** handler errors are logged (not fatal)

#### Scenario: Event ordering guarantees for concurrent operations
- **GIVEN** multiple concurrent task operations (e.g., create, update, complete)
- **WHEN** operations occur simultaneously on the same or different tasks
- **THEN** events for each operation are emitted in a deterministic order:
  - Each operation's events are emitted sequentially (not concurrent)
  - Operations on different tasks may have interleaved events (not guaranteed global ordering)
  - Within a single operation, events fire in order (e.g., update event fires before completion event if both triggered)
- **AND** all handlers for an event complete before the next event is dispatched (sequential per-event dispatch)
- **AND** handler execution does NOT block the main operation from completing

#### Scenario: Reentrancy and event suppression
- **GIVEN** a hook handler that calls a task service method (e.g., handler calls `complete_task()`)
- **WHEN** service method would normally emit an event
- **THEN** event emission is suppressed to prevent infinite loops (reentrancy guard)
- **AND** handlers MUST declare which API surface they use to prevent unexpected cascading events
- **AND** if reentrancy is detected, a warning is logged with the handler name

#### Scenario: User can define custom handlers
- **GIVEN** a user creates `~/.tasky/hooks.py`
- **WHEN** tasky starts
- **THEN** hooks from user file are loaded and registered
- **AND** custom handlers can access the event object
- **AND** custom handlers can make external API calls (Slack, etc.)

### Requirement: Hook Error Handling

If a hook fails, it SHALL not prevent the core operation from completing or other hooks from executing.

**Error Class Conventions:** All hook-related exceptions MUST inherit from `TaskDomainError` (from `tasky_tasks.exceptions`), following the project's domain error hierarchy. This ensures exception handling in CLI and service layers correctly catches and processes hook failures.

#### Scenario: Handler exception doesn't break operation
- **GIVEN** an external hook that calls a broken API endpoint
- **WHEN** a task is completed (triggering the hook)
- **THEN** the task is still completed successfully
- **AND** the hook exception is logged
- **AND** other hooks still execute
- **AND** user sees warning in logs (if verbose)

#### Scenario: Invalid user hooks are handled gracefully
- **GIVEN** user has defined `~/.tasky/hooks.py` with syntax error
- **WHEN** tasky starts
- **THEN** error is logged during hook loading
- **AND** other hooks still load (if syntax is valid)
- **AND** core tasky functionality is not impaired

#### Scenario: Load-time hook validation and error recovery
- **GIVEN** user has defined `~/.tasky/hooks.py` with import error (e.g., missing dependency)
- **WHEN** hook loader attempts to import the file
- **THEN** loader catches the import exception
- **AND** error is logged with details: file path, exception message, line number if available
- **AND** hook loading is skipped for that file (system continues with built-in hooks)
- **AND** subsequent task operations work normally (core functionality unimpaired)

#### Scenario: Runtime handler validation and isolation
- **GIVEN** a registered handler that raises an exception during execution
- **WHEN** task operation triggers the handler (e.g., task completion triggers hook)
- **THEN** handler exception is caught and logged (not fatal)
- **AND** exception message, handler name, and event type are logged
- **AND** other handlers for the same event continue to execute
- **AND** the original task operation completes successfully (task is completed despite hook failure)

#### Scenario: Hook reentrancy guard prevents infinite loops
- **GIVEN** a handler that calls a task service method (e.g., `complete_task()`)
- **WHEN** that service method would emit an event that triggers the same handler
- **THEN** system detects reentrancy and suppresses the nested event emission
- **AND** warning is logged: "Reentrancy detected in handler <name>; event suppressed to prevent loop"
- **AND** the handler call completes without cascading events
- **AND** handler implementation must document which API surface it uses

#### Scenario: Non-callable hook definitions are validated
- **GIVEN** user defines `~/.tasky/hooks.py` with invalid handlers (e.g., class instead of function, variable instead of callable)
- **WHEN** hook loader processes the file
- **THEN** loader validates each exported symbol is callable
- **AND** non-callable exports are logged as warnings: "Hook <name> is not callable; skipping"
- **AND** other valid hooks continue to load
- **AND** core functionality continues unimpaired

### Requirement: CLI Hook Integration

The CLI SHALL support verbose hook output and allow users to observe hook execution.

#### Scenario: Verbose output shows hook execution
- **GIVEN** user runs `tasky task create "my task" --verbose-hooks`
- **WHEN** task is created
- **THEN** console output includes "Hook: TaskCreatedEvent fired" or similar
- **AND** hook details are shown in readable format
- **AND** hook status (success/failure) is visible
- **AND** handler names and execution times are logged

#### Scenario: Default hook behavior (no verbose flag)
- **GIVEN** user runs `tasky task create "my task"` (without flags)
- **WHEN** task is created
- **THEN** hooks are emitted and execute normally
- **AND** detailed hook output is NOT shown (quiet by default)
- **AND** only critical hook failures are logged to console

#### Scenario: Disable hooks with --no-hooks flag
- **GIVEN** user runs `tasky task create "my task" --no-hooks`
- **WHEN** task is created
- **THEN** hook emission is completely disabled
- **AND** no handlers are called (including default logging handlers)
- **AND** task operation completes as normal (hooks are completely transparent)
- **AND** useful for batch operations or performance-sensitive scenarios

#### Scenario: Quiet mode suppresses hook output
- **GIVEN** user runs `tasky task create "my task" --quiet`
- **WHEN** task is created
- **THEN** hook logging output is suppressed
- **AND** hooks still execute (default handlers still log to file/debug level)
- **AND** but console output is silent
- **AND** useful for scripting or non-interactive use

#### Scenario: Verbose flag respects global log level
- **GIVEN** user runs `tasky --log-level INFO task create "my task" --verbose-hooks`
- **WHEN** task is created
- **THEN** verbose hook output only shows if global log level permits (DEBUG or lower for detailed output)
- **AND** INFO-level hooks are shown regardless of --verbose-hooks
- **AND** DEBUG-level hook details only shown if global log is set to DEBUG
- **AND** --verbose-hooks flag can override to force DEBUG output for hooks only

#### Scenario: Hooks work with all task commands
- **WHEN** user runs any task command (create, update, complete, delete)
- **THEN** appropriate hooks are emitted
- **AND** hooks work consistently across all commands
- **AND** default handlers (logging) always execute
- **AND** flags (--verbose-hooks, --no-hooks, --quiet) apply to all commands

### Requirement: Hook Event Schema

All events SHALL follow a consistent schema with required metadata fields.

#### Scenario: Event includes metadata
- **GIVEN** any task lifecycle event
- **WHEN** event is created
- **THEN** event includes:
  - event_type (string, e.g., "task_created")
  - timestamp (ISO 8601 datetime)
  - task_id (UUID)
  - project_root (Path)
  - And event-specific data (task snapshot, old values, etc.)

#### Scenario: Events are serializable with datetime and timezone support
- **GIVEN** a TaskCreatedEvent with timestamp and due_date fields
- **WHEN** event is serialized to JSON
- **THEN** all datetime fields are serialized as ISO 8601 strings with timezone (e.g., "2025-11-15T14:30:45Z")
- **AND** timezone information is preserved (not lost)
- **AND** null dates are serialized as null (not errors)
- **AND** event can be logged or exported
- **AND** event can be reconstructed from JSON with identical datetime values
- **AND** deserialization produces a task object with correct datetime type

#### Scenario: JSON serialization handles nested and complex structures
- **GIVEN** a task event with nested structures (subtasks, blockers, tags, custom fields)
- **WHEN** event is serialized to JSON
- **THEN** nested arrays and objects are properly serialized
- **AND** serialization is stable (same event always produces identical JSON)
- **AND** null values are handled consistently (included as null, not omitted)
- **AND** round-trip serialization (to JSON and back) produces identical data
- **AND** example JSON includes:
  ```json
  {
    "event_type": "task_created",
    "schema_version": "1.0",
    "timestamp": "2025-11-15T14:30:45Z",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "project_root": "/home/user/projects/myapp",
    "task_snapshot": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Fix login bug",
      "details": "Users cannot login with SSO",
      "priority": "high",
      "due_date": "2025-12-01T00:00:00Z",
      "status": "pending",
      "created_at": "2025-11-15T14:30:45Z",
      "updated_at": "2025-11-15T14:30:45Z",
      "tags": ["bug", "urgent"],
      "subtasks": [],
      "blocked_by": []
    }
  }
  ```

#### Scenario: Schema versioning for backward/forward compatibility
- **GIVEN** event emission system
- **WHEN** event is created
- **THEN** every event includes `schema_version: str` field (e.g., "1.0")
- **AND** schema version follows semantic versioning (major.minor)
- **AND** deserialization checks schema_version to apply migrations if needed
- **AND** backward compatibility: if schema_version < current, apply migration steps
- **AND** forward compatibility: if schema_version > current, log warning but continue (new fields ignored)
- **AND** migration example: if schema_version="0.9", map old field names to new names during deserialization
- **AND** migration policy documents breaking changes in CHANGELOG with schema version bumps

#### Scenario: Event round-trip reconstruction for replay/audit
- **GIVEN** a TaskCreatedEvent serialized to JSON and stored
- **WHEN** event is deserialized from JSON
- **THEN** all fields match the original event exactly
- **AND** timestamps are identical (millisecond precision preserved)
- **AND** task state can be reconstructed for audit or replay scenarios
- **AND** test requirement: event → JSON → event roundtrip must be lossless for all event types
