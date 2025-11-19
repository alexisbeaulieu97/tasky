## 1. Hook Event Types Definition

Each event MUST be implemented as a Pydantic `BaseModel` in `packages/tasky-hooks/events.py` with:
- Shared base class `BaseEvent(BaseModel)` with `event_type: str` and `timestamp: datetime` fields
- Immutability enforced via `model_config = ConfigDict(frozen=True)`
- Use Pydantic's standard serialization (`.model_dump(mode="json")` and `.model_dump_json()`)
- Schema version field: `schema_version: str = "1.0"` on every event
- Follow project naming convention: event classes end with `Event` (e.g., `TaskCreatedEvent`)

### 1.1 Define `TaskCreatedEvent` with task snapshot
- [x] 1.1a Create `TaskCreatedEvent` class inheriting from `BaseEvent`
- [x] 1.1b Add fields: task_id, task_snapshot (TaskModel), project_root
- [x] 1.1c Ensure serializable (can be converted to dict and JSON)
- [x] 1.1d Write unit tests for model creation, immutability, and serialization

### 1.2 Define `TaskUpdatedEvent` with old and new snapshots
- [x] 1.2a Create `TaskUpdatedEvent` class inheriting from `BaseEvent`
- [x] 1.2b Add fields: task_id, old_snapshot, new_snapshot, updated_fields (list of field names)
- [x] 1.2c Ensure serializable
- [x] 1.2d Write tests verifying old/new snapshots are identical except for updated fields

### 1.3 Define `TaskCompletedEvent` with completion timestamp
- [x] 1.3a Create `TaskCompletedEvent` class inheriting from `BaseEvent`
- [x] 1.3b Add fields: task_id, task_snapshot, completion_timestamp (ISO 8601)
- [x] 1.3c Ensure serializable
- [x] 1.3d Write tests for timestamp handling

### 1.4 Define `TaskCancelledEvent` with reason (optional)
- [x] 1.4a Create `TaskCancelledEvent` class inheriting from `BaseEvent`
- [x] 1.4b Add fields: task_id, task_snapshot, reason (str | None), previous_status
- [x] 1.4c Ensure serializable
- [x] 1.4d Write tests for optional reason field handling

### 1.5 Define `TaskReopenedEvent` with previous status
- [x] 1.5a Create `TaskReopenedEvent` class inheriting from `BaseEvent`
- [x] 1.5b Add fields: task_id, task_snapshot, previous_status, new_status
- [x] 1.5c Ensure serializable
- [x] 1.5d Write tests verifying status transitions are captured

### 1.6 Define `TaskDeletedEvent` with task snapshot
- [x] 1.6a Create `TaskDeletedEvent` class inheriting from `BaseEvent`
- [x] 1.6b Add fields: task_id, task_snapshot (full state before deletion)
- [x] 1.6c Ensure serializable
- [x] 1.6d Write tests ensuring full snapshot is captured before deletion

### 1.7 Define `TasksImportedEvent` with count and results
- [x] 1.7a Create `TasksImportedEvent` class inheriting from `BaseEvent`
- [x] 1.7b Add fields: import_count, skipped_count, failed_count, import_strategy, imported_task_ids (list)
- [x] 1.7c Ensure serializable
- [x] 1.7d Write tests for count aggregation

### 1.8 Event Serialization & Round-trip Tests
- [x] 1.8a Write unit tests for each event's `.model_dump()` and `.model_dump_json()` methods
- [x] 1.8b Write round-trip test for each event: event → `.model_dump_json()` → `.model_validate_json()` → identical event
- [x] 1.8c Test datetime serialization (ISO 8601 with timezone preserved, Pydantic standard)
- [x] 1.8d Test nested structures (task snapshots with subtasks, tags, blockers via nested model serialization)
- [x] 1.8e Test null value handling (optional fields serialized as JSON null, not omitted)
- [x] 1.8f Verify immutability: attempts to modify event fields after creation raise Pydantic ValidationError

## 2. Hook Dispatcher Implementation

- [x] 2.1 Create `dispatcher.py` with `HookDispatcher` class
- [x] 2.2 Implement event registration (subscribe to event type)
- [x] 2.3 Implement event broadcasting (notify all subscribers)
- [x] 2.4 Implement handler error handling (don't let one handler fail others)
- [x] 2.5 Create global dispatcher instance
- [x] 2.6 Write unit tests for dispatcher (register, broadcast, error handling)

## 3. Default Hook Handlers

- [x] 3.1 Create `handlers.py` with default handlers
- [x] 3.2 Implement logging handler (logs all events)
- [x] 3.3 Implement optional CLI echo handler (prints events to stdout)
- [x] 3.4 Add configuration flag for verbose hook output
- [x] 3.5 Write tests for default handlers

## 4. Task Service Integration

- [x] 4.1 Update `TaskService.create_task()` to emit `TaskCreatedEvent`
- [x] 4.2 Update `TaskService.update_task()` to emit `TaskUpdatedEvent`
- [x] 4.3 Update `TaskService.complete_task()` to emit `TaskCompletedEvent`
- [x] 4.4 Update `TaskService.cancel_task()` to emit `TaskCancelledEvent`
- [x] 4.5 Update `TaskService.reopen_task()` to emit `TaskReopenedEvent`
- [x] 4.6 Update `TaskService.delete_task()` to emit `TaskDeletedEvent`
- [x] 4.7 Update task import logic to emit `TasksImportedEvent`
- [x] 4.8 Write integration tests (service methods emit correct events)

## 5. CLI Integration

- [x] 5.1 Add `--verbose-hooks` flag to CLI
- [x] 5.2 Enable hook output when flag is set
- [x] 5.3 Test with create, update, complete, delete commands
- [x] 5.4 Verify hook output appears in correct format

## 6. Hook Extension Points

- [x] 6.1 Create `user_hooks.py` module for user-defined hooks (location: `~/.tasky/hooks.py`)
- [x] 6.2 Implement hook loading from user config file
- [x] 6.3 Add error handling for malformed user hooks
- [ ] 6.4 Create example user hook file (template)
- [ ] 6.5 Write tests for hook loading and execution

## 7. Documentation & Examples

- [ ] 7.1 Create `HOOKS.md` documentation
- [ ] 7.2 Document all event types and their payloads
- [ ] 7.3 Provide example: logging to external file
- [ ] 7.4 Provide example: Slack notification webhook
- [ ] 7.5 Provide example: calendar integration
- [ ] 7.6 Document configuration and error handling
- [ ] 7.7 Create template user hooks file

## 8. Advanced Features (Optional)

- [ ] 8.1 Implement async hook support (if needed for external APIs)
- [ ] 8.2 Add hook retry logic with exponential backoff
- [ ] 8.3 Add hook timeout enforcement
- [ ] 8.4 Create hook registry/plugin system
- [ ] 8.5 Document plugin API

## 9. Testing & Validation

### 9.1-9.3: Coverage & Code Quality
- [x] 9.1 Run `uv run pytest packages/tasky-hooks/ --cov` (verify ≥80% coverage)
- [x] 9.2a Update service unit/integration tests to assert event emission for all CRUD methods
  - [x] 9.2a.1 Add test: `TaskService.create_task()` emits `TaskCreatedEvent` with correct fields
  - [x] 9.2a.2 Add test: `TaskService.update_task()` emits `TaskUpdatedEvent` with old/new snapshots
  - [x] 9.2a.3 Add test: `TaskService.complete_task()` emits `TaskCompletedEvent`
  - [x] 9.2a.4 Add test: `TaskService.cancel_task()` emits `TaskCancelledEvent`
  - [x] 9.2a.5 Add test: `TaskService.reopen_task()` emits `TaskReopenedEvent`
  - [x] 9.2a.6 Add test: `TaskService.delete_task()` emits `TaskDeletedEvent`
  - [ ] 9.2a.7 Add test: `TaskService.import_tasks()` emits `TasksImportedEvent`
- [x] 9.2b Add tests for hook error handling and retry/rollback behavior in service context
  - [x] 9.2b.1 Test: Handler exception during event emission doesn't prevent task operation
  - [x] 9.2b.2 Test: Multiple handlers execute even if one fails
  - [ ] 9.2b.3 Test: Handler exceptions are logged with context (handler name, event type, error)
- [ ] 9.3 Run full test suite `uv run pytest --cov=packages --cov-fail-under=80` (verify overall coverage)

### 9.4-9.5: End-to-End & Integration Tests
- [x] 9.4a Add automated integration test for CLI → service → hook dispatch flow
  - [x] 9.4a.1 Test: `tasky task create "test" --verbose-hooks` emits and shows hook output
  - [x] 9.4a.2 Test: `tasky task update <id> --name "updated" --verbose-hooks` shows update event
  - [ ] 9.4a.3 Test: `tasky task complete <id> --verbose-hooks` shows completion event
  - [ ] 9.4a.4 Test: `tasky task delete <id> --verbose-hooks` shows deletion event
  - [ ] 9.4a.5 Test: `tasky task create ... --no-hooks` suppresses all hook output
  - [ ] 9.4a.6 Test: `tasky task create ... --quiet` suppresses verbose hook details
- [ ] 9.4b Add test verifying verbose hook output formatting and content
  - [ ] 9.4b.1 Test: `--verbose-hooks` shows handler names and execution status
  - [ ] 9.4b.2 Test: `--verbose-hooks` shows event type and task_id
  - [ ] 9.4b.3 Test: Failed handler shows error message and does not prevent other handlers
  - [ ] 9.4b.4 Test: Handler output respects global log level (only DEBUG/TRACE show all details)
- [ ] 9.5 Run `uv run ruff check --fix` (format code)
- [ ] 9.6 Run `uv run pyright` (static type checking)

## 10. Post-Implementation

- [ ] 10.1 Add examples to documentation
- [ ] 10.2 Create default user hooks template
- [ ] 10.3 Consider future: async hook support
- [ ] 10.4 Consider future: hook metrics/telemetry
