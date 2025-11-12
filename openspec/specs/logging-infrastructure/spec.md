# logging-infrastructure Specification

## Purpose
TBD - created by archiving change add-hierarchical-configuration. Update Purpose after archive.
## Requirements
### Requirement: Logging configuration must accept settings object

The `configure_logging()` function SHALL accept a `LoggingSettings` object instead of individual parameters. This enables settings-driven configuration and supports the hierarchical configuration system.

#### Scenario: configure_logging accepts LoggingSettings

- **GIVEN** a `LoggingSettings` object with `verbosity=1` and `format="standard"`
- **WHEN** `configure_logging(settings)` is called
- **THEN** logging is configured with INFO level
- **AND** logs use standard format
- **AND** the function no longer accepts raw `verbosity` and `format_style` parameters

#### Scenario: LoggingSettings is imported from tasky_settings

- **WHEN** tasky-logging needs to type-hint `LoggingSettings`
- **THEN** it uses `TYPE_CHECKING` import from tasky_settings.models
- **AND** there is no runtime dependency on tasky-settings
- **AND** the import is for type checking only

---

### Requirement: CLI must configure logging from settings system

The CLI callback MUST load settings using `get_settings()` and pass the logging settings to `configure_logging()`. This replaces direct construction of logging parameters.

#### Scenario: CLI loads settings and configures logging

- **WHEN** the CLI main callback is executed
- **THEN** it calls `get_settings(cli_overrides=...)` with CLI flag overrides
- **AND** it calls `configure_logging(settings.logging)`
- **AND** it no longer directly constructs verbosity values

#### Scenario: CLI verbose flag becomes override in settings

- **GIVEN** user runs `tasky -vv task list`
- **WHEN** the CLI callback processes the verbose flag
- **THEN** it creates `cli_overrides = {"logging": {"verbosity": 2}}`
- **AND** passes overrides to `get_settings(cli_overrides=...)`
- **AND** the settings system merges with file configs and env vars

---

### Requirement: Logging configuration can be persisted in config files

Users MUST be able to persist logging preferences in global or project configuration files. This eliminates the need to specify verbosity flags on every command.

#### Scenario: Global config sets default verbosity

- **GIVEN** `~/.tasky/config.toml` contains `logging.verbosity = 1`
- **WHEN** any command is run without `-v` flag
- **THEN** logging operates at INFO level
- **AND** the preference applies to all projects

#### Scenario: Project config overrides global verbosity

- **GIVEN** global config sets `logging.verbosity = 0`
- **AND** project config sets `logging.verbosity = 2`
- **WHEN** a command is run in the project directory
- **THEN** logging operates at DEBUG level
- **AND** the project setting overrides the global default

#### Scenario: CLI flag overrides config files

- **GIVEN** any config files set verbosity values
- **WHEN** a command is run with `-v` or `-vv` flag
- **THEN** the CLI flag takes precedence
- **AND** config file settings are ignored for verbosity

---

### Requirement: Logging format can be configured in settings

Users MUST be able to configure log output format through settings. Supported formats include "standard", "json", and "minimal".

#### Scenario: Standard format is configured via settings

- **GIVEN** config contains `logging.format = "standard"`
- **WHEN** logging is configured
- **THEN** logs include timestamp, logger name, level, and message
- **AND** the format matches the existing standard format

#### Scenario: Minimal format reduces log verbosity

- **GIVEN** config contains `logging.format = "minimal"`
- **WHEN** logging is configured
- **THEN** logs only include level and message
- **AND** timestamp and logger name are omitted

#### Scenario: JSON format enables structured logging

- **GIVEN** config contains `logging.format = "json"`
- **WHEN** logging is configured
- **THEN** logs are output as JSON objects
- **AND** each log line is valid JSON (future implementation)

---

### Requirement: Logging configuration maintains backward compatibility

The logging package MUST continue to work without configuration files. Missing configs should use sensible defaults and not cause errors.

#### Scenario: Logging works without config files

- **GIVEN** no config files exist
- **WHEN** `get_settings()` is called
- **THEN** default logging settings are used (verbosity=0, format="standard")
- **AND** logging functions correctly
- **AND** no errors or warnings occur

#### Scenario: Logging package can be used independently

- **WHEN** code imports and uses tasky-logging without tasky-settings
- **THEN** logging functions work correctly
- **AND** `get_logger()` returns functional loggers
- **AND** type hints for LoggingSettings are optional

---

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

