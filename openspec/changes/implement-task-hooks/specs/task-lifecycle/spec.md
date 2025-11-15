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
- **THEN** appropriate event is emitted (TaskCompletedEvent, etc.)
- **AND** event includes previous status, new status, timestamp
- **AND** handlers receive event immediately

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

#### Scenario: User can define custom handlers
- **GIVEN** a user creates `~/.tasky/hooks.py`
- **WHEN** tasky starts
- **THEN** hooks from user file are loaded and registered
- **AND** custom handlers can access the event object
- **AND** custom handlers can make external API calls (Slack, etc.)

### Requirement: Hook Error Handling

If a hook fails, it SHALL not prevent the core operation from completing or other hooks from executing.

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

### Requirement: CLI Hook Integration

The CLI SHALL support verbose hook output and allow users to observe hook execution.

#### Scenario: Verbose output shows hook execution
- **GIVEN** user runs `tasky task create "my task" --verbose-hooks`
- **WHEN** task is created
- **THEN** console output includes "Hook: TaskCreatedEvent fired" or similar
- **AND** hook details are shown in readable format
- **AND** hook status (success/failure) is visible

#### Scenario: Hooks work with all task commands
- **WHEN** user runs any task command (create, update, complete, delete)
- **THEN** appropriate hooks are emitted
- **AND** hooks work consistently across all commands
- **AND** default handlers (logging) always execute

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

#### Scenario: Events are serializable
- **GIVEN** a TaskCreatedEvent
- **WHEN** event is serialized to JSON
- **THEN** all fields are properly serialized
- **AND** event can be logged or exported
- **AND** event can be reconstructed from JSON
