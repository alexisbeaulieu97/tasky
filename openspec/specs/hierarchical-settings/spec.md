# hierarchical-settings Specification

## Purpose
TBD - created by archiving change add-hierarchical-configuration. Update Purpose after archive.
## Requirements
### Requirement: Settings must be defined with type-safe models

The `tasky-settings` package SHALL provide Pydantic models for all application settings. Settings models MUST include validation rules, default values, and documentation. This enables type checking, IDE autocomplete, and runtime validation.

#### Scenario: LoggingSettings model defines logging configuration

- **WHEN** code imports `LoggingSettings` from tasky-settings
- **THEN** the model includes `verbosity: int` field with range 0-2
- **AND** the model includes `format: Literal["standard", "json", "minimal"]` field
- **AND** default values are provided for all fields
- **AND** the model is a Pydantic BaseModel with validation

#### Scenario: TaskDefaultsSettings model defines task creation defaults

- **WHEN** code imports `TaskDefaultsSettings` from tasky-settings
- **THEN** the model includes `priority: int` field with range 1-5
- **AND** the model includes `status: str` field with default value
- **AND** validation ensures only valid values are accepted

#### Scenario: AppSettings composes subsystem settings

- **WHEN** code imports `AppSettings` from tasky-settings
- **THEN** the model includes `logging: LoggingSettings` field
- **AND** the model includes `task_defaults: TaskDefaultsSettings` field
- **AND** the model inherits from pydantic_settings.BaseSettings
- **AND** the model configures env var prefix "TASKY_"

---

### Requirement: Custom sources must load configuration from TOML files

The `tasky-settings` package SHALL provide custom pydantic-settings sources that load configuration from TOML files. Sources MUST handle missing files gracefully and provide meaningful error messages for malformed files.

#### Scenario: TomlConfigSource loads valid TOML file

- **GIVEN** a TOML file exists at a specified path
- **WHEN** TomlConfigSource is instantiated with that path
- **THEN** the source loads and parses the TOML file
- **AND** returns a dictionary of configuration values
- **AND** the dictionary structure matches the TOML structure

#### Scenario: TomlConfigSource handles missing files gracefully

- **GIVEN** a TOML file does not exist at the specified path
- **WHEN** TomlConfigSource is instantiated with that path
- **THEN** the source returns an empty dictionary
- **AND** no exception is raised
- **AND** default values from models are used

#### Scenario: TomlConfigSource reports parsing errors

- **GIVEN** a TOML file exists but contains invalid TOML syntax
- **WHEN** TomlConfigSource attempts to load the file
- **THEN** the source returns an empty dictionary
- **AND** logs a warning about the parsing error (optional)
- **AND** application continues with defaults

---

### Requirement: GlobalConfigSource must load from user home directory

The `tasky-settings` package SHALL provide GlobalConfigSource that loads from `~/.tasky/config.toml`. This source provides user-wide default settings that apply to all projects.

#### Scenario: GlobalConfigSource uses correct file path

- **WHEN** GlobalConfigSource is instantiated
- **THEN** it targets `~/.tasky/config.toml` (expanding ~ to user home)
- **AND** it creates parent directories if needed for future save operations
- **AND** it inherits from TomlConfigSource

#### Scenario: GlobalConfigSource loads user defaults

- **GIVEN** `~/.tasky/config.toml` contains `[logging]\nverbosity = 1`
- **WHEN** settings are loaded with GlobalConfigSource
- **THEN** `settings.logging.verbosity` equals 1
- **AND** these values apply to all projects by default

---

### Requirement: ProjectConfigSource must load from project directory

The `tasky-settings` package SHALL provide ProjectConfigSource that loads from `.tasky/config.toml` relative to a project root. This source provides project-specific settings that override global settings.

#### Scenario: ProjectConfigSource uses project root parameter

- **GIVEN** a project root path is provided
- **WHEN** ProjectConfigSource is instantiated with that path
- **THEN** it targets `<project_root>/.tasky/config.toml`
- **AND** it inherits from TomlConfigSource

#### Scenario: ProjectConfigSource defaults to current directory

- **GIVEN** no project root is specified
- **WHEN** ProjectConfigSource is instantiated
- **THEN** it uses `Path.cwd()` as the project root
- **AND** targets `.tasky/config.toml` in current directory

---

### Requirement: Settings must merge from multiple sources with correct precedence

The `tasky-settings` package SHALL provide a `get_settings()` function that merges configuration from multiple sources. Sources MUST be applied in order: defaults → global config → project config → environment variables → CLI overrides (last wins).

#### Scenario: Later sources override earlier sources

- **GIVEN** global config sets `logging.verbosity = 0`
- **AND** project config sets `logging.verbosity = 1`
- **WHEN** `get_settings()` is called from the project directory
- **THEN** `settings.logging.verbosity` equals 1 (project wins)

#### Scenario: CLI overrides take highest precedence

- **GIVEN** global config sets `logging.verbosity = 0`
- **AND** project config sets `logging.verbosity = 1`
- **AND** CLI overrides include `{"logging": {"verbosity": 2}}`
- **WHEN** `get_settings(cli_overrides=...)` is called
- **THEN** `settings.logging.verbosity` equals 2 (CLI wins)

#### Scenario: Environment variables override file configs

- **GIVEN** global config sets `logging.verbosity = 0`
- **AND** environment variable `TASKY_LOGGING__VERBOSITY=2` is set
- **WHEN** `get_settings()` is called
- **THEN** `settings.logging.verbosity` equals 2 (env var wins)
- **AND** env vars use double underscore for nesting

#### Scenario: Missing configurations use model defaults

- **GIVEN** no config files exist
- **AND** no environment variables are set
- **AND** no CLI overrides provided
- **WHEN** `get_settings()` is called
- **THEN** all settings use default values from Pydantic models
- **AND** application functions normally

---

### Requirement: Settings must validate configuration values

The `tasky-settings` package SHALL validate all configuration values using Pydantic validation. Invalid values MUST raise clear validation errors that identify the problem and provide guidance.

#### Scenario: Invalid verbosity value is rejected

- **GIVEN** a config file contains `logging.verbosity = 5`
- **WHEN** `get_settings()` is called
- **THEN** a validation error is raised
- **AND** the error message indicates verbosity must be 0-2
- **AND** the error identifies the source (file path)

#### Scenario: Invalid field type is rejected

- **GIVEN** a config file contains `logging.verbosity = "high"`
- **WHEN** `get_settings()` is called
- **THEN** a validation error is raised
- **AND** the error message indicates verbosity must be an integer
- **AND** the error identifies the field and source

#### Scenario: Unknown fields are ignored

- **GIVEN** a config file contains `logging.unknown_field = true`
- **WHEN** `get_settings()` is called with default Pydantic config
- **THEN** the unknown field is ignored (no error)
- **AND** valid fields are still loaded correctly

---

### Requirement: Settings factory must accept project root parameter

The `get_settings()` function SHALL accept an optional `project_root` parameter to specify where to find `.tasky/config.toml`. This enables testing and supports explicit project paths.

#### Scenario: Explicit project root is used

- **GIVEN** a project exists at `/path/to/project/`
- **AND** that project has `.tasky/config.toml`
- **WHEN** `get_settings(project_root=Path("/path/to/project"))` is called
- **THEN** settings are loaded from `/path/to/project/.tasky/config.toml`
- **AND** the current working directory is not used

#### Scenario: None project root uses current directory

- **GIVEN** the current directory is `/path/to/project/`
- **WHEN** `get_settings(project_root=None)` is called
- **THEN** settings are loaded from `/path/to/project/.tasky/config.toml`
- **AND** `Path.cwd()` is used as project root

---

### Requirement: Settings must be independently testable

The `tasky-settings` package SHALL include comprehensive unit tests that verify models, sources, precedence, and validation without depending on other tasky packages.

#### Scenario: Settings models can be validated in isolation

- **WHEN** tests instantiate `LoggingSettings(verbosity=1)`
- **THEN** validation passes
- **AND** no imports from tasky-tasks or tasky-cli are needed

#### Scenario: Custom sources can be tested with temporary files

- **WHEN** tests create a temporary TOML file
- **AND** instantiate TomlConfigSource with that path
- **THEN** the source correctly loads the file
- **AND** the test cleans up the temporary file

#### Scenario: Precedence rules are verified with multiple sources

- **WHEN** tests set up multiple config sources with conflicting values
- **AND** call `get_settings()` with those sources
- **THEN** the correct precedence order is verified
- **AND** the highest priority source wins

---

