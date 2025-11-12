# storage-configuration Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
### Requirement: Storage settings model

The system SHALL provide a `StorageSettings` Pydantic model for configuring storage backend selection and options.

#### Scenario: Create storage settings with defaults

```gherkin
Given StorageSettings model is available
When I instantiate StorageSettings()
Then backend defaults to "json"
And path defaults to "tasks.json"
```

#### Scenario: Create storage settings with custom values

```gherkin
Given StorageSettings model is available
When I instantiate StorageSettings(backend="sqlite", path="data/tasks.db")
Then backend is "sqlite"
And path is "data/tasks.db"
```

#### Scenario: Use storage settings in AppSettings

```gherkin
Given AppSettings has a storage field of type StorageSettings
When I load AppSettings with [storage] section in config
Then settings.storage.backend contains the configured backend
And settings.storage.path contains the configured path
```

---

### Requirement: Storage settings in hierarchical configuration

Storage configuration SHALL respect the hierarchical precedence system from `add-hierarchical-configuration`.

#### Scenario: Storage settings from project config

```gherkin
Given a project with .tasky/config.toml containing:
  """
  [storage]
  backend = "sqlite"
  path = "data/tasks.db"
  """
When I call get_settings() from project root
Then settings.storage.backend == "sqlite"
And settings.storage.path == "data/tasks.db"
```

#### Scenario: Environment variable overrides project config

```gherkin
Given project config specifies backend="json"
And environment variable TASKY_STORAGE_BACKEND="sqlite"
When I call get_settings()
Then settings.storage.backend == "sqlite"
```

#### Scenario: Default values when not configured

```gherkin
Given no .tasky/config.toml exists
And no environment variables are set
When I call get_settings()
Then settings.storage.backend == "json"
And settings.storage.path == "tasks.json"
```

---

### Requirement: Storage settings validation

Storage settings SHALL validate backend names and paths appropriately.

#### Scenario: Valid backend name

```gherkin
Given a backend name "json"
When I create StorageSettings(backend="json")
Then validation succeeds
```

#### Scenario: Empty backend name rejected

```gherkin
Given an empty backend name ""
When I try to create StorageSettings(backend="")
Then Pydantic validation raises an error
```

---

