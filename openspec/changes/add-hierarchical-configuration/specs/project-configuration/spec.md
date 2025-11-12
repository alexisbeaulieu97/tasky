# Specification Delta: Project Configuration

**Change ID**: `add-hierarchical-configuration`
**Capability**: `project-configuration`
**Type**: New Capability

---

## ADDED Requirements

### Requirement: Project configuration must be stored in .tasky directory

The application SHALL store project-specific configuration in `.tasky/config.toml` relative to the project root. This file provides settings that override global configuration and apply only to the specific project.

#### Scenario: Project config file location is .tasky directory

- **WHEN** the application looks for project configuration
- **THEN** it checks `.tasky/config.toml` in the project root
- **AND** the file is optional (missing file uses global/defaults)
- **AND** the `.tasky/` directory is the project identifier

#### Scenario: Project config is independent per project

- **GIVEN** two projects exist with different `.tasky/config.toml` files
- **WHEN** commands are run in each project
- **THEN** each project uses its own configuration
- **AND** settings do not leak between projects

---

### Requirement: Project configuration must override global settings

Project-specific configuration MUST take precedence over global configuration but be overridden by CLI flags and environment variables. This creates a three-tier hierarchy: global → project → runtime.

#### Scenario: Project overrides global logging settings

- **GIVEN** global config sets `logging.verbosity = 0`
- **AND** project config sets `logging.verbosity = 2`
- **WHEN** a command is run in the project directory
- **THEN** the logging verbosity is 2 (project wins over global)

#### Scenario: Environment variables override project config

- **GIVEN** project config sets `logging.verbosity = 1`
- **AND** environment variable `TASKY_LOGGING__VERBOSITY=2` is set
- **WHEN** a command is run in the project directory
- **THEN** the logging verbosity is 2 (env var wins over project)

#### Scenario: CLI flags override project config

- **GIVEN** project config sets `logging.verbosity = 1`
- **WHEN** a command is run with `-vv` flag
- **THEN** the logging verbosity is 2 (CLI flag wins over project)

---

### Requirement: Project configuration must support same settings as global

The project configuration file SHALL support all the same settings as global configuration. This ensures consistent schema across configuration levels.

#### Scenario: Project can override logging settings

- **GIVEN** project config contains:
  ```toml
  [logging]
  verbosity = 2
  format = "json"
  ```
- **WHEN** a command is run in the project
- **THEN** logging uses DEBUG verbosity and JSON format
- **AND** these settings override global configuration

#### Scenario: Project can override task defaults

- **GIVEN** project config contains:
  ```toml
  [task_defaults]
  priority = 5
  status = "pending"
  ```
- **WHEN** a task is created in the project
- **THEN** the task uses priority 5 and status "pending"
- **AND** these settings override global task defaults

---

### Requirement: Project configuration must be discovered from current directory

The application SHALL locate the project configuration by checking for `.tasky/config.toml` starting from the current working directory. For MVP, only the current directory is checked.

#### Scenario: Project config found in current directory

- **GIVEN** the current directory is `/path/to/project/`
- **AND** `/path/to/project/.tasky/config.toml` exists
- **WHEN** a command is run
- **THEN** that config file is loaded
- **AND** the current directory is treated as project root

#### Scenario: Missing project config uses defaults

- **GIVEN** the current directory has no `.tasky/config.toml`
- **WHEN** a command is run
- **THEN** global configuration and defaults are used
- **AND** no error occurs
- **AND** the application functions normally

#### Scenario: Project root can be explicitly specified

- **GIVEN** the `get_settings()` function accepts a `project_root` parameter
- **WHEN** `get_settings(project_root=Path("/explicit/path"))` is called
- **THEN** project config is loaded from `/explicit/path/.tasky/config.toml`
- **AND** the current directory is not used

---

### Requirement: Project configuration must be TOML format

The project configuration file MUST use TOML format, matching the global configuration format for consistency.

#### Scenario: Project config uses TOML syntax

- **GIVEN** `.tasky/config.toml` contains valid TOML
- **WHEN** the file is loaded
- **THEN** all TOML features are supported (comments, sections, nested values)
- **AND** the format matches global config for consistency

#### Scenario: Invalid TOML is reported clearly

- **GIVEN** `.tasky/config.toml` contains syntax errors
- **WHEN** a command attempts to load the config
- **THEN** a clear error message is shown
- **AND** the error identifies the file path
- **AND** the error describes the syntax problem

---

### Requirement: Project configuration file is optional

The project configuration file MUST be optional. Applications should work correctly when no project config exists, using global configuration and built-in defaults.

#### Scenario: Commands work without project config

- **GIVEN** no `.tasky/config.toml` file exists
- **AND** no global config exists
- **WHEN** any tasky command is run
- **THEN** the command executes successfully
- **AND** built-in defaults are used
- **AND** no errors or warnings are shown

#### Scenario: Partial project config works

- **GIVEN** project config only specifies:
  ```toml
  [logging]
  verbosity = 2
  ```
- **WHEN** the config is loaded
- **THEN** `logging.verbosity` is 2
- **AND** all other settings use global config or defaults
- **AND** no validation errors occur for missing fields

---

## Dependencies

- **Depends on**: `hierarchical-settings` (uses ProjectConfigSource)
- **Depended on by**: None
- **Coordinates with**: `add-configurable-storage-backends` (will add `storage` section later)

---

## Coordination Notes

### Integration with Storage Backends Change

This capability creates `.tasky/config.toml` for project configuration. The `add-configurable-storage-backends` change (not yet implemented) will later add a `storage` section to this same file.

**Current scope (this change)**:
```toml
[logging]
verbosity = 2

[task_defaults]
priority = 5
```

**Future scope (storage backends change)**:
```toml
[logging]
verbosity = 2

[task_defaults]
priority = 5

[storage]
backend = "json"
path = "tasks.json"
```

The hierarchical settings infrastructure created by this change will support the storage configuration when that change is implemented. No refactoring will be needed - just adding fields to `AppSettings`.

---

## Migration Notes

- Project configuration is optional - no action required for existing projects
- Projects can create `.tasky/config.toml` to customize settings
- Existing `.tasky/` directories are not affected
- When storage backends change lands, existing config files will be extended with `storage` section
