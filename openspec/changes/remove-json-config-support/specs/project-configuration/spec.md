## MODIFIED Requirements

### Requirement: Project configuration must be stored in TOML format only

The application SHALL store project-specific configuration exclusively in `.tasky/config.toml` format. Legacy JSON configuration support has been removed. Any attempt to load `.tasky/config.json` will result in a clear error message directing users to migrate.

#### Scenario: Project config is TOML format

- **GIVEN** a project with `.tasky/config.toml`
- **WHEN** the application loads project configuration
- **THEN** the TOML file is successfully loaded
- **AND** all TOML features are supported (comments, sections, nested values)

#### Scenario: Missing TOML config uses defaults

- **GIVEN** no `.tasky/config.toml` exists (and no `.tasky/config.json`)
- **WHEN** a command is run
- **THEN** global configuration and defaults are used
- **AND** no error occurs

#### Scenario: Missing TOML config raises file not found error

- **GIVEN** a project exists with `.tasky/config.json` (old format)
- **AND** no `.tasky/config.toml` exists
- **WHEN** the application attempts to load project configuration
- **THEN** an error is raised with message: "Config file not found: .tasky/config.toml"
- **AND** no mention of JSON, legacy formats, or migration
- **AND** the error is identical to any other missing config scenario

#### Scenario: Invalid TOML is reported clearly

- **GIVEN** `.tasky/config.toml` contains syntax errors
- **WHEN** a command attempts to load the config
- **THEN** a clear error message is shown
- **AND** the error identifies the file path
- **AND** the error describes the syntax problem

---

### Requirement: Project configuration must override global settings

Project-specific configuration MUST take precedence over global configuration but be overridden by CLI flags and environment variables. This three-tier hierarchy is unchanged from v1.0.

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

---

### Requirement: Project configuration must support same settings as global

The project configuration file SHALL support all the same settings as global configuration.

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

#### Scenario: Project config found in current directory

- **GIVEN** the current directory is `/path/to/project/`
- **AND** `/path/to/project/.tasky/config.toml` exists
- **WHEN** a command is run
- **THEN** that config file is loaded
- **AND** the current directory is treated as project root

#### Scenario: Project root can be explicitly specified

- **GIVEN** the `get_settings()` function accepts a `project_root` parameter
- **WHEN** `get_settings(project_root=Path("/explicit/path"))` is called
- **THEN** project config is loaded from `/explicit/path/.tasky/config.toml`
- **AND** the current directory is not used

---

### Requirement: Project configuration file is optional

The project configuration file MUST be optional. Applications should work correctly when no project config exists.

#### Scenario: Commands work without project config

- **GIVEN** no `.tasky/config.toml` file exists
- **AND** no `.tasky/` directory exists
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

---

## REMOVED Requirements

### Requirement: Project configuration must support JSON format (legacy)

**Reason**: JSON format support was deprecated in v1.0 in favor of TOML. After providing a full v1.x release cycle for users to migrate, JSON support is now removed.

**Migration**: Users with `.tasky/config.json` files from v0.x must manually convert to TOML format. Refer to release notes and migration guide for detailed instructions.

**Code Removal**:
- JSON detection logic in `ProjectConfig.from_file()` removed
- `_load_json()` helper method removed
- JSON-specific test cases removed (~12-15 tests)
- Migration warning log statements removed
