# project-configuration Specification

## Purpose
TBD - created by archiving change add-hierarchical-configuration. Update Purpose after archive.
## Requirements
### Requirement: Project configuration must be stored in .tasky directory

The application SHALL store project-specific configuration in `.tasky/config.toml` relative to the project root. The `.tasky/config.json` legacy file SHALL NOT be loaded, auto-converted, or treated as a valid configuration source. Users MUST create or maintain the TOML file themselves when project-specific overrides are required.

#### Scenario: Project config file location is .tasky directory with TOML format

- **WHEN** the application looks for project configuration
- **THEN** it checks `.tasky/config.toml` in the project root
- **AND** the `.tasky/` directory is the project identifier

#### Scenario: Legacy JSON config is rejected

- **GIVEN** a project contains `.tasky/config.json`
- **AND** no `.tasky/config.toml` exists
- **WHEN** the application loads project configuration
- **THEN** the JSON file is ignored
- **AND** the loader raises an error: "Config file not found: .tasky/config.toml" with guidance to migrate to TOML
- **AND** no automatic JSON-to-TOML conversion occurs

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

The application SHALL locate the project configuration by checking for `.tasky/config.toml` starting from the current working directory.

#### Scenario: Missing project config uses defaults

- **GIVEN** the current directory has no `.tasky/config.toml`
- **WHEN** a command is run
- **THEN** global configuration and defaults are used
- **AND** no error occurs
- **AND** the application functions normally

#### Scenario: Project root can be explicitly specified

- **GIVEN** the `get_settings()` function accepts a `project_root` parameter
- **WHEN** `get_settings(project_root=Path("/explicit/path"))` is called
- **THEN** project config is loaded only from `/explicit/path/.tasky/config.toml`
- **AND** `.tasky/config.json` is ignored even if present
- **AND** the current directory is not used

---

### Requirement: Project configuration must be TOML format

The project configuration file MUST use TOML format, matching the global configuration format for consistency.

#### Scenario: Project config uses TOML syntax

- **GIVEN** `.tasky/config.toml` contains valid TOML
- **WHEN** the file is loaded
- **THEN** all TOML features are supported (comments, sections, nested values)
- **AND** the format matches global config for consistency

#### Scenario: Legacy JSON format is unsupported

- **GIVEN** a project contains `.tasky/config.json`
- **WHEN** the application attempts to load the config
- **THEN** the operation fails with the message: "Config file not found: .tasky/config.toml"
- **AND** guidance directs the user to convert the file to TOML
- **AND** no JSON parsing occurs

### Requirement: Project configuration file is optional

The project configuration file MUST be optional. Applications should work correctly when no project config exists, using global configuration and built-in defaults.

#### Scenario: Commands work without project config

- **GIVEN** no `.tasky/config.toml` file exists
- **AND** no `.tasky/config.json` file exists
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

### Requirement: ProjectConfig class must serialize to TOML format

The `ProjectConfig` helper in `tasky-projects` SHALL provide `from_file()` and `to_file()` helpers that read and write `.tasky/config.toml` files using TOML serialization so the domain layer matches the storage format.

#### Scenario: ProjectConfig reads TOML files

- **GIVEN** a valid TOML file containing project metadata and `[storage]` configuration
- **WHEN** `ProjectConfig.from_file(Path(".tasky/config.toml"))` is called
- **THEN** a populated `ProjectConfig` instance is returned
- **AND** storage backend and path fields reflect the TOML contents
- **AND** datetime fields (such as `created_at`) are parsed as timezone-aware values

#### Scenario: ProjectConfig writes TOML files

- **GIVEN** a `ProjectConfig` instance with custom values
- **WHEN** `config.to_file(Path(".tasky/config.toml"))` is called
- **THEN** the target directory is created if necessary
- **AND** the resulting file uses valid TOML syntax with `[storage]` sections
- **AND** a subsequent `from_file()` round-trip returns the same values

#### Scenario: ProjectConfig reports invalid TOML

- **GIVEN** `.tasky/config.toml` contains invalid TOML
- **WHEN** `ProjectConfig.from_file()` is called
- **THEN** a parsing error is raised that identifies the file as malformed

---

### Requirement: ProjectConfig must use binary file mode for TOML operations

`ProjectConfig.from_file()` MUST open configuration files in binary read mode (`"rb"`), and `ProjectConfig.to_file()` MUST open files in binary write mode (`"wb"`) to satisfy the expectations of `tomllib` and `tomli_w`.

#### Scenario: Binary mode on read

- **GIVEN** a project configuration file exists
- **WHEN** `ProjectConfig.from_file()` executes
- **THEN** the file handle is opened in `"rb"` mode without an explicit encoding
- **AND** TOML parsing succeeds

#### Scenario: Binary mode on write

- **GIVEN** any `ProjectConfig` instance
- **WHEN** `config.to_file()` executes
- **THEN** the destination file is opened in `"wb"` mode with no encoding parameter
- **AND** TOML serialization succeeds

