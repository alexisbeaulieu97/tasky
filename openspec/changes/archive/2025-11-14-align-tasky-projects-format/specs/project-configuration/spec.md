## MODIFIED Requirements

### Requirement: ProjectConfig class must serialize to TOML format

The `ProjectConfig` class in `tasky-projects` package SHALL use TOML format for file I/O operations, matching the system-wide configuration format. The class provides `from_file()` and `to_file()` methods that read and write TOML files using `tomllib` (read) and `tomli_w` (write).

#### Scenario: ProjectConfig reads TOML file successfully

- **GIVEN** a valid TOML file at `/path/to/config.toml` containing:
  ```toml
  version = "1.0"
  created_at = "2025-11-12T10:00:00Z"

  [storage]
  backend = "json"
  path = "tasks.json"
  ```
- **WHEN** `ProjectConfig.from_file(Path("/path/to/config.toml"))` is called
- **THEN** a `ProjectConfig` instance is returned
- **AND** `config.version` equals `"1.0"`
- **AND** `config.storage.backend` equals `"json"`
- **AND** `config.storage.path` equals `"tasks.json"`
- **AND** `config.created_at` is a valid datetime

#### Scenario: ProjectConfig writes TOML file successfully

- **GIVEN** a `ProjectConfig` instance with version "1.0" and storage backend "sqlite"
- **WHEN** `config.to_file(Path("/path/to/config.toml"))` is called
- **THEN** a file is created at `/path/to/config.toml`
- **AND** the file contains valid TOML syntax
- **AND** the file includes sections like `[storage]`
- **AND** the file is human-readable with proper formatting

#### Scenario: ProjectConfig round-trip preserves data

- **GIVEN** a `ProjectConfig` instance with custom values
- **WHEN** the config is saved with `to_file()` and reloaded with `from_file()`
- **THEN** all fields match the original values
- **AND** datetime fields preserve timezone information
- **AND** nested objects (like `storage`) are correctly deserialized

#### Scenario: ProjectConfig handles invalid TOML

- **GIVEN** a file containing invalid TOML syntax
- **WHEN** `ProjectConfig.from_file()` is called on that file
- **THEN** a `tomllib.TOMLDecodeError` is raised
- **AND** the error message identifies the syntax problem

#### Scenario: ProjectConfig creates parent directories

- **GIVEN** a config path with non-existent parent directories
- **WHEN** `config.to_file(Path("/new/nested/dir/config.toml"))` is called
- **THEN** all parent directories are created
- **AND** the TOML file is written successfully

---

## ADDED Requirements

### Requirement: ProjectConfig must use binary file mode for TOML operations

The `ProjectConfig` class SHALL open files in binary mode (`"rb"` for reading, `"wb"` for writing) when performing TOML serialization, as required by the `tomllib` and `tomli_w` libraries.

#### Scenario: from_file opens file in binary read mode

- **GIVEN** a TOML configuration file
- **WHEN** `ProjectConfig.from_file()` is called
- **THEN** the file is opened in binary read mode (`"rb"`)
- **AND** no encoding parameter is specified (not needed for binary mode)
- **AND** TOML parsing succeeds

#### Scenario: to_file opens file in binary write mode

- **GIVEN** a `ProjectConfig` instance
- **WHEN** `config.to_file()` is called
- **THEN** the file is opened in binary write mode (`"wb"`)
- **AND** no encoding parameter is specified (not needed for binary mode)
- **AND** TOML writing succeeds

---

## REMOVED Requirements

None.
