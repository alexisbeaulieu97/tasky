# Change: Implement Task Lifecycle Hooks

## Why

Tasky currently has a `tasky-hooks` package that defines hook contracts but no actual hook implementation or dispatcher. Users cannot automate workflows based on task events. A working hooks system enables:

- User-defined automation (trigger scripts on task creation, completion, etc.)
- External system integration (Slack notifications, calendar updates, etc.)
- Extensibility without modifying core code (plugins can hook into lifecycle)
- Event-driven architecture for future features (audit logs, analytics, etc.)

## What Changes

- Implement `tasky-hooks` hook dispatcher and event broadcasting
- Create 7 core lifecycle events (created, updated, completed, cancelled, reopened, deleted, imported)
- Build default event handlers (logging, optional CLI output)
- Add hook registration and execution infrastructure
- Integrate hooks into task service methods
- Add CLI flag for verbose hook output
- Create user-facing hook documentation and examples

## Impact

- **Affected specs**: New `task-lifecycle` spec, extends `task-domain` spec
- **Affected code**: `packages/tasky-hooks/`, `packages/tasky-tasks/service.py`, `packages/tasky-cli/`
- **Backward compatibility**: Fully additive; no breaking changes
- **Feature**: Event-driven architecture foundation for future automation
