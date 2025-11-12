# Specification Delta: Global Configuration

**Change ID**: `add-hierarchical-configuration`
**Capability**: `global-configuration`
**Type**: New Capability

---

## ADDED Requirements

### Requirement: Global configuration must be stored in user home directory

The application SHALL store user-wide configuration in `~/.tasky/config.toml`. This file provides default settings that apply to all projects for the current user.

#### Scenario: Global config file location is user home

- **WHEN** the application looks for global configuration
- **THEN** it checks `~/.tasky/config.toml`
- **AND** the `~` is expanded to the user's home directory
- **AND** the file is optional (missing file uses defaults)

#### Scenario: Global config directory is created on demand

- **GIVEN** `~/.tasky/` directory does not exist
- **WHEN** the application needs to save global configuration
- **THEN** the `~/.tasky/` directory is created
- **AND** appropriate permissions are set (user read/write only)

---

### Requirement: Global configuration must support logging settings

The global configuration file SHALL support logging settings that apply to all projects. Users can set default verbosity and format preferences.

#### Scenario: Global logging verbosity is applied

- **GIVEN** `~/.tasky/config.toml` contains:
  ```toml
  [logging]
  verbosity = 1
  ```
- **WHEN** any tasky command is run without CLI verbosity flags
- **THEN** the logging verbosity is set to 1 (INFO level)
- **AND** this applies to all projects

#### Scenario: Global logging format is applied

- **GIVEN** `~/.tasky/config.toml` contains:
  ```toml
  [logging]
  format = "minimal"
  ```
- **WHEN** any tasky command is run
- **THEN** logs use the minimal format
- **AND** this applies to all projects

---

### Requirement: Global configuration must support task defaults

The global configuration file SHALL support default task settings that apply when tasks are created. This includes default priority, status, and other task attributes.

#### Scenario: Global task priority default is applied

- **GIVEN** `~/.tasky/config.toml` contains:
  ```toml
  [task_defaults]
  priority = 5
  ```
- **WHEN** a task is created without explicit priority
- **THEN** the task is assigned priority 5
- **AND** this applies across all projects

#### Scenario: Global task status default is applied

- **GIVEN** `~/.tasky/config.toml` contains:
  ```toml
  [task_defaults]
  status = "in_progress"
  ```
- **WHEN** a task is created without explicit status
- **THEN** the task is assigned status "in_progress"
- **AND** this applies across all projects

---

### Requirement: Global configuration can be overridden by project config

Project-specific configuration MUST take precedence over global configuration. This allows users to customize settings per project while maintaining global defaults.

#### Scenario: Project config overrides global logging verbosity

- **GIVEN** `~/.tasky/config.toml` contains `logging.verbosity = 0`
- **AND** `.tasky/config.toml` contains `logging.verbosity = 2`
- **WHEN** a command is run in the project directory
- **THEN** the logging verbosity is 2 (project wins)
- **AND** the global setting is ignored for this project

#### Scenario: Project config partially overrides global settings

- **GIVEN** global config contains:
  ```toml
  [logging]
  verbosity = 1
  format = "standard"
  ```
- **AND** project config contains:
  ```toml
  [logging]
  verbosity = 2
  ```
- **WHEN** a command is run in the project directory
- **THEN** `logging.verbosity` is 2 (from project)
- **AND** `logging.format` is "standard" (from global)
- **AND** settings are merged, not replaced entirely

---

### Requirement: Global configuration must be TOML format

The global configuration file MUST use TOML format for human readability and Python ecosystem compatibility. Comments should be preserved when possible.

#### Scenario: Global config supports TOML comments

- **GIVEN** `~/.tasky/config.toml` contains:
  ```toml
  # Logging configuration
  [logging]
  verbosity = 1  # INFO level for all projects
  ```
- **WHEN** the file is loaded
- **THEN** comments are supported by the parser
- **AND** comments provide documentation for users

#### Scenario: Global config uses TOML nested sections

- **GIVEN** `~/.tasky/config.toml` uses nested sections
- **WHEN** the file is loaded
- **THEN** nested sections are correctly parsed
- **AND** dotted keys (`logging.verbosity`) work in code

---

## Dependencies

- **Depends on**: `hierarchical-settings` (uses GlobalConfigSource)
- **Depended on by**: None

---

## Migration Notes

- Global configuration is optional - no user action required
- Users can create `~/.tasky/config.toml` to customize defaults
- Example config files should be provided in documentation
- No migration needed for existing users (file doesn't exist yet)
