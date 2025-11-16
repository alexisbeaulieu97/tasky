# Change: Refactor CLI Error Handling

## Why

Error handling in `packages/tasky-cli/src/tasky_cli/commands/tasks.py` is scattered across multiple helper functions (`_handle_task_domain_error`, `_handle_storage_error`, `_handle_registry_error`, etc.) that duplicate exception matching and formatting logic. A consolidated error dispatcher will:

- Eliminate duplicated exception handling code
- Make it easier to add new exception types without modifying multiple functions
- Centralize exit code and message formatting policy
- Improve maintainability as domain exceptions evolve

## What Changes

- Extract error handlers into a dedicated `error_dispatcher.py` module with registry-based dispatch
- Move all `_handle_*` functions into the new module
- Update `with_task_error_handling` decorator to use the new dispatcher
- Maintain identical error messages and exit codes (no user-visible changes)

## Impact

- **Affected specs**: `cli-error-presentation` (enhance with dispatcher pattern)
- **Affected code**: `packages/tasky-cli/src/tasky_cli/commands/tasks.py`, new `packages/tasky-cli/src/tasky_cli/error_dispatcher.py`
- **Backward compatibility**: Error messages and exit codes unchanged; refactoring only
