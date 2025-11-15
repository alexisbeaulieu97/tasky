## 1. Hook Event Types Definition

- [ ] 1.1 Define `TaskCreatedEvent` with task snapshot
- [ ] 1.2 Define `TaskUpdatedEvent` with old and new snapshots
- [ ] 1.3 Define `TaskCompletedEvent` with completion timestamp
- [ ] 1.4 Define `TaskCancelledEvent` with reason (optional)
- [ ] 1.5 Define `TaskReopenedEvent` with previous status
- [ ] 1.6 Define `TaskDeletedEvent` with task snapshot
- [ ] 1.7 Define `TasksImportedEvent` with count and results
- [ ] 1.8 Write tests for event model serialization

## 2. Hook Dispatcher Implementation

- [ ] 2.1 Create `dispatcher.py` with `HookDispatcher` class
- [ ] 2.2 Implement event registration (subscribe to event type)
- [ ] 2.3 Implement event broadcasting (notify all subscribers)
- [ ] 2.4 Implement handler error handling (don't let one handler fail others)
- [ ] 2.5 Create global dispatcher instance
- [ ] 2.6 Write unit tests for dispatcher (register, broadcast, error handling)

## 3. Default Hook Handlers

- [ ] 3.1 Create `handlers.py` with default handlers
- [ ] 3.2 Implement logging handler (logs all events)
- [ ] 3.3 Implement optional CLI echo handler (prints events to stdout)
- [ ] 3.4 Add configuration flag for verbose hook output
- [ ] 3.5 Write tests for default handlers

## 4. Task Service Integration

- [ ] 4.1 Update `TaskService.create_task()` to emit `TaskCreatedEvent`
- [ ] 4.2 Update `TaskService.update_task()` to emit `TaskUpdatedEvent`
- [ ] 4.3 Update `TaskService.complete_task()` to emit `TaskCompletedEvent`
- [ ] 4.4 Update `TaskService.cancel_task()` to emit `TaskCancelledEvent`
- [ ] 4.5 Update `TaskService.reopen_task()` to emit `TaskReopenedEvent`
- [ ] 4.6 Update `TaskService.delete_task()` to emit `TaskDeletedEvent`
- [ ] 4.7 Update task import logic to emit `TasksImportedEvent`
- [ ] 4.8 Write integration tests (service methods emit correct events)

## 5. CLI Integration

- [ ] 5.1 Add `--verbose-hooks` flag to CLI
- [ ] 5.2 Enable hook output when flag is set
- [ ] 5.3 Test with create, update, complete, delete commands
- [ ] 5.4 Verify hook output appears in correct format

## 6. Hook Extension Points

- [ ] 6.1 Create `user_hooks.py` module for user-defined hooks (location: `~/.tasky/hooks.py`)
- [ ] 6.2 Implement hook loading from user config file
- [ ] 6.3 Add error handling for malformed user hooks
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

- [ ] 9.1 Run `uv run pytest packages/tasky-hooks/ --cov`
- [ ] 9.2 Run `uv run pytest packages/tasky-tasks/ --cov` (verify service integration)
- [ ] 9.3 Run full test suite `uv run pytest --cov=packages --cov-fail-under=80`
- [ ] 9.4 Verify hooks work end-to-end (CLI → service → hook dispatch)
- [ ] 9.5 Run `uv run ruff check --fix`
- [ ] 9.6 Run `uv run pyright`

## 10. Post-Implementation

- [ ] 10.1 Add examples to documentation
- [ ] 10.2 Create default user hooks template
- [ ] 10.3 Consider future: async hook support
- [ ] 10.4 Consider future: hook metrics/telemetry
