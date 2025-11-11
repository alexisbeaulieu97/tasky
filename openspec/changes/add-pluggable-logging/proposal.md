# Change: Pluggable Logging System

## Why

The application currently lacks observability and debugging capabilities. Users and developers have no insight into what the application is doing, making troubleshooting difficult. This change introduces a pluggable logging system that:

- Provides visibility into application operations
- Supports swappable logging backends (stdlib logging by default, loguru in future)
- Allows verbosity control via CLI flags
- Maintains clean architecture by keeping logging concerns separate

## What Changes

- Create new `tasky-logging` package with logging abstraction
- Implement `Logger` protocol for dependency injection
- Provide `get_logger(name)` factory function using stdlib logging
- Implement `configure_logging(verbosity, format_style)` for CLI integration
- Add logging calls to `TaskService` methods (create, update, delete, etc.)
- Add logging calls to `JsonTaskRepository` operations
- Update CLI main entry point to accept `--verbose` flag and configure logging
- Add CLI callback to configure logging before command execution

## Impact

- **Affected specs**: `logging-infrastructure` (new capability)
- **Affected code**: 
  - `packages/tasky-logging/` (new package)
  - `packages/tasky-tasks/src/tasky_tasks/service.py` (add logging)
  - `packages/tasky-storage/src/tasky_storage/backends/json/repository.py` (add logging)
  - `packages/tasky-cli/src/tasky_cli/__init__.py` (add verbosity control)
- **Backward compatibility**: Compatible - purely additive, no breaking changes
- **Dependencies**: 
  - `tasky-tasks` gains optional dependency on `tasky-logging`
  - `tasky-storage` gains optional dependency on `tasky-logging`
  - `tasky-cli` gains required dependency on `tasky-logging`
