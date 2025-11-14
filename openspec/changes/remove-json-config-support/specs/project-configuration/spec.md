## MODIFIED Requirements

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
