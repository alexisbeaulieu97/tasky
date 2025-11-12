# Specification Delta: Logging Infrastructure

**Change ID**: `add-hierarchical-configuration`
**Capability**: `logging-infrastructure`
**Type**: Modification

---

## MODIFIED Requirements

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

## Dependencies

- **Depends on**: `hierarchical-settings` (provides LoggingSettings model)
- **Depended on by**: CLI, task service, storage repositories

---

## Migration Notes

- **Breaking change**: `configure_logging(verbosity, format_style)` becomes `configure_logging(settings)`
- Migration required in CLI callback to use settings system
- Existing logging calls in services/repositories unchanged (no breaking changes there)
- Tests that call `configure_logging()` directly need to pass settings object
