# Change: Add CLI Input Validators

## Why

CLI commands currently mix input parsing, validation, and business logic calls together in single functions. This scatters validation rules across multiple command handlers and makes error messages inconsistent. A dedicated validator layer will:

- Consolidate validation logic in one place (easier to maintain and extend)
- Fail fast with user-friendly messages before creating services
- Make validation testable without invoking service layers
- Ensure consistent error formatting across all commands

## What Changes

- Add new `cli-input-validation` capability with validator protocols and implementations
- Create `packages/tasky-cli/src/tasky_cli/validators.py` module with dedicated validators
- Update command handlers to use validators before service invocation
- Remove scattered validation helper functions from task and project commands

## Impact

- **Affected specs**: `task-cli-operations`, `project-cli-operations`, new `cli-input-validation`
- **Affected code**: `packages/tasky-cli/src/tasky_cli/commands/tasks.py`, `packages/tasky-cli/src/tasky_cli/commands/projects.py`
- **Backward compatibility**: CLI behavior unchanged; commands produce identical error messages
