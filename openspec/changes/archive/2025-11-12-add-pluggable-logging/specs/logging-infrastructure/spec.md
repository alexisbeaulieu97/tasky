# Specification Delta: Logging Infrastructure

**Change ID**: `add-pluggable-logging`  
**Capability**: `logging-infrastructure`  
**Type**: New Capability

---

## ADDED Requirements

### Requirement: Package must provide logger abstraction protocol

The `tasky-logging` package SHALL provide a `Logger` Protocol that defines the interface for logging operations. This protocol enables dependency injection and allows swapping logging implementations without changing consumer code.

#### Scenario: Logger protocol defines standard methods

- **GIVEN** the `tasky-logging` package is imported
- **WHEN** code references the `Logger` Protocol
- **THEN** the protocol includes methods for debug, info, warning, error, and critical logging
- **AND** the protocol can be used for type hints in consuming packages

---

### Requirement: Package must provide logger factory function

The `tasky-logging` package SHALL provide a `get_logger(name: str)` factory function that returns a configured logger instance. The function MUST accept a logger name and return a logger scoped to that name with the prefix "tasky.".

#### Scenario: get_logger returns namespaced logger

- **WHEN** code calls `get_logger("tasks.service")`
- **THEN** a logger instance is returned
- **AND** the logger name is "tasky.tasks.service"
- **AND** the logger can be used to log messages

#### Scenario: Multiple get_logger calls return consistent loggers

- **GIVEN** code calls `get_logger("test")` twice
- **WHEN** both loggers are compared
- **THEN** they refer to the same underlying logger instance
- **AND** configuration applies to both references

---

### Requirement: Package must provide logging configuration

The `tasky-logging` package SHALL provide a `configure_logging(verbosity: int, format_style: str)` function that configures the logging system. The function MUST support multiple verbosity levels and format styles.

#### Scenario: configure_logging sets log level based on verbosity

- **WHEN** `configure_logging(verbosity=0)` is called
- **THEN** the root tasky logger level is set to WARNING
- **AND** only WARNING, ERROR, and CRITICAL messages are emitted

#### Scenario: verbosity level 1 enables INFO logs

- **WHEN** `configure_logging(verbosity=1)` is called
- **THEN** the root tasky logger level is set to INFO
- **AND** INFO, WARNING, ERROR, and CRITICAL messages are emitted
- **AND** DEBUG messages are not emitted

#### Scenario: verbosity level 2+ enables DEBUG logs

- **WHEN** `configure_logging(verbosity=2)` is called
- **THEN** the root tasky logger level is set to DEBUG
- **AND** all log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) are emitted

#### Scenario: configure_logging supports standard format

- **WHEN** `configure_logging(format_style="standard")` is called
- **THEN** log messages include timestamp, logger name, level, and message
- **AND** the format is human-readable

---

### Requirement: Logging must be usable without explicit configuration

The `tasky-logging` package SHALL provide sensible defaults that allow logging to work without calling `configure_logging()`. Unconfigured loggers MUST emit WARNING-level and above messages to stderr.

#### Scenario: Logger works before configuration

- **GIVEN** `configure_logging()` has not been called
- **WHEN** code obtains a logger via `get_logger()` and logs a warning
- **THEN** the warning message is emitted to stderr
- **AND** no errors or exceptions occur

---

### Requirement: TaskService operations must be logged

The `TaskService` SHALL log all task operations (create, read, update, delete) at appropriate levels. INFO-level logs MUST be emitted for mutating operations (create, update, delete) and DEBUG-level logs for read operations.

#### Scenario: Creating a task logs at INFO level

- **WHEN** `TaskService.create_task()` is called with name and details
- **THEN** an INFO-level log message is emitted
- **AND** the log includes the operation ("create_task") and task ID
- **AND** the task is created successfully

#### Scenario: Updating a task logs at INFO level

- **WHEN** `TaskService.update_task()` is called with a task
- **THEN** an INFO-level log message is emitted
- **AND** the log includes the operation ("update_task") and task ID
- **AND** the task is updated successfully

#### Scenario: Deleting a task logs at INFO level

- **WHEN** `TaskService.delete_task()` is called with a task ID
- **THEN** an INFO-level log message is emitted
- **AND** the log includes the operation ("delete_task") and task ID
- **AND** the task is deleted successfully

#### Scenario: Reading a task logs at DEBUG level

- **WHEN** `TaskService.get_task()` is called with a task ID
- **THEN** a DEBUG-level log message is emitted
- **AND** the log includes the operation ("get_task") and task ID
- **AND** the task is retrieved successfully

#### Scenario: Listing all tasks logs at DEBUG level

- **WHEN** `TaskService.get_all_tasks()` is called
- **THEN** a DEBUG-level log message is emitted
- **AND** the log includes the operation ("get_all_tasks") and count of tasks retrieved
- **AND** all tasks are retrieved successfully

---

### Requirement: Repository operations must be logged

The `JsonTaskRepository` SHALL log all persistence operations at DEBUG level. This provides insight into file I/O operations and helps troubleshoot storage issues.

#### Scenario: Saving a task logs at DEBUG level

- **WHEN** `JsonTaskRepository.save_task()` is called
- **THEN** a DEBUG-level log message is emitted
- **AND** the log includes the operation ("save_task") and task ID
- **AND** the task is persisted to storage

#### Scenario: Loading a task logs at DEBUG level

- **WHEN** `JsonTaskRepository.get_task()` is called
- **THEN** a DEBUG-level log message is emitted
- **AND** the log includes the operation ("get_task") and task ID
- **AND** the task is loaded from storage

#### Scenario: Storage errors log at WARNING level

- **GIVEN** the JSON file is corrupted or inaccessible
- **WHEN** a repository operation is attempted
- **THEN** a WARNING-level log message is emitted
- **AND** the log includes the error details
- **AND** the error is propagated to the caller

---

### Requirement: CLI must support verbosity control

The CLI application SHALL support a `--verbose` flag that can be repeated to increase logging verbosity. The flag MUST be available globally and configure logging before command execution.

#### Scenario: CLI runs with default verbosity (no flag)

- **WHEN** a command is run without `--verbose` flag
- **THEN** only WARNING-level and above logs are shown
- **AND** the command executes normally

#### Scenario: CLI runs with single verbose flag

- **WHEN** a command is run with `-v` or `--verbose`
- **THEN** INFO-level and above logs are shown
- **AND** the command executes normally
- **AND** user sees informational messages about operations

#### Scenario: CLI runs with double verbose flag

- **WHEN** a command is run with `-vv` or `--verbose --verbose`
- **THEN** DEBUG-level and above logs are shown
- **AND** the command executes normally
- **AND** user sees detailed debugging information

#### Scenario: Verbose flag works with all commands

- **GIVEN** the verbose flag is specified
- **WHEN** any task or project command is run
- **THEN** logging is configured before the command executes
- **AND** log output reflects the specified verbosity level
- **AND** the command functionality is unaffected

---

### Requirement: Logging implementation must be swappable

The logging infrastructure MUST be designed to allow replacing the stdlib logging implementation with alternatives (e.g., loguru) by only modifying the `tasky-logging` package. Consumer packages MUST depend only on the `Logger` protocol and factory function.

#### Scenario: Swapping to loguru requires no consumer changes

- **GIVEN** `get_logger()` is implemented using loguru internally
- **WHEN** consumer packages use `get_logger()`
- **THEN** logging works correctly with loguru
- **AND** no changes are needed in `tasky-tasks`, `tasky-storage`, or `tasky-cli`
- **AND** the `Logger` protocol is still satisfied

---

### Requirement: Package must be independently testable

The `tasky-logging` package SHALL include comprehensive unit tests that verify logging configuration, logger creation, and output behavior. Tests MUST not require other tasky packages.

#### Scenario: Logger factory tests pass independently

- **WHEN** tests in `tasky-logging/tests/` are run
- **THEN** all tests for `get_logger()` pass
- **AND** no dependencies on other tasky packages are required

#### Scenario: Configuration tests verify verbosity levels

- **WHEN** tests call `configure_logging()` with different verbosity values
- **THEN** the correct log level is set for each value
- **AND** the tests can verify the level via logger inspection

---

## Dependencies

- **Depends on**: None (uses Python stdlib only)
- **Depended on by**: 
  - `tasky-tasks` (optional dependency for service logging)
  - `tasky-storage` (optional dependency for repository logging)
  - `tasky-cli` (required dependency for verbosity control)

---

## Migration Notes

- Purely additive change - no breaking changes to existing APIs
- Existing code continues to work without logging
- Logging can be adopted incrementally in different packages
- No changes needed to existing test suites
