# Capability: Project Configuration

**Status**: Draft  
**Capability ID**: `project-configuration`  
**Package**: `tasky-projects`

---

## ADDED Requirements

### Requirement: Project configuration model

The system SHALL provide a Pydantic model for project-level configuration that includes storage backend settings, versioning, and metadata.

#### Scenario: Load configuration from JSON file

```gherkin
Given a file ".tasky/config.json" exists with content:
  """
  {
    "version": "1.0",
    "storage": {
      "backend": "json",
      "path": "tasks.json"
    },
    "created_at": "2025-11-11T10:00:00Z"
  }
  """
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then it returns a ProjectConfig instance
And config.version == "1.0"
And config.storage.backend == "json"
And config.storage.path == "tasks.json"
And config.created_at is a timezone-aware datetime in UTC
```

#### Scenario: Save configuration to JSON file

```gherkin
Given a ProjectConfig instance with:
  | field               | value                    |
  | version             | "1.0"                    |
  | storage.backend     | "sqlite"                 |
  | storage.path        | "tasks.db"               |
  | created_at          | 2025-11-11T15:30:00Z     |
When I call config.to_file(Path(".tasky/config.json"))
Then a file ".tasky/config.json" is created
And the file contains valid JSON matching the config values
And the parent directory ".tasky" is created if it doesn't exist
```

#### Scenario: Default values for storage configuration

```gherkin
Given I create a StorageConfig with no arguments
Then storage_config.backend == "json"
And storage_config.path == "tasks.json"
```

#### Scenario: Default values for project configuration

```gherkin
Given I create a ProjectConfig with no arguments
Then config.version == "1.0"
And config.storage is a StorageConfig with default values
And config.created_at is set to the current UTC time
```

---

### Requirement: Configuration validation

The system SHALL validate configuration values and raise descriptive errors for invalid input.

#### Scenario: Reject invalid JSON

```gherkin
Given a file ".tasky/config.json" with invalid JSON:
  """
  { invalid json }
  """
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then it raises a validation error
And the error message indicates JSON parsing failed
```

#### Scenario: Reject missing required fields

```gherkin
Given a file ".tasky/config.json" with content:
  """
  {
    "version": "1.0"
  }
  """
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then it raises a validation error
And the error message indicates "storage" field is required
```

#### Scenario: Reject invalid field types

```gherkin
Given a file ".tasky/config.json" with content:
  """
  {
    "version": 1.0,
    "storage": "not-an-object",
    "created_at": "2025-11-11T10:00:00Z"
  }
  """
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then it raises a validation error
And the error message indicates type mismatch for "version" or "storage"
```

---

### Requirement: File not found handling

The system SHALL raise a clear error when attempting to load a non-existent configuration file.

#### Scenario: Missing configuration file

```gherkin
Given the file ".tasky/config.json" does not exist
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then it raises FileNotFoundError
And the error message includes the path ".tasky/config.json"
```

---

### Requirement: UTC timezone enforcement

The system SHALL ensure all timestamps in the configuration are timezone-aware and use UTC.

#### Scenario: Created timestamp uses UTC

```gherkin
Given I create a ProjectConfig with no created_at argument
Then config.created_at.tzinfo is not None
And config.created_at.tzinfo is UTC
```

#### Scenario: Loaded timestamp is timezone-aware

```gherkin
Given a file ".tasky/config.json" with:
  """
  {
    "version": "1.0",
    "storage": {"backend": "json", "path": "tasks.json"},
    "created_at": "2025-11-11T10:00:00Z"
  }
  """
When I call ProjectConfig.from_file(Path(".tasky/config.json"))
Then config.created_at.tzinfo is not None
And config.created_at.tzinfo is UTC
```

---

## Implementation Notes

### Package Structure

```
packages/tasky-projects/
├── src/tasky_projects/
│   ├── __init__.py              # Exports ProjectConfig, StorageConfig
│   └── config.py                # Configuration models
├── tests/
│   └── test_config.py           # Configuration tests
└── pyproject.toml
```

### Key Classes

```python
class StorageConfig(BaseModel):
    """Storage backend configuration."""
    backend: str = Field(default="json")
    path: str = Field(default="tasks.json")

class ProjectConfig(BaseModel):
    """Project configuration model."""
    version: str = Field(default="1.0")
    storage: StorageConfig = Field(default_factory=StorageConfig)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    
    @classmethod
    def from_file(cls, path: Path) -> "ProjectConfig":
        """Load configuration from JSON file."""
        ...
    
    def to_file(self, path: Path) -> None:
        """Save configuration to JSON file."""
        ...
```

### Dependencies

```toml
[project]
name = "tasky-projects"
requires-python = ">=3.13"
dependencies = ["pydantic>=2.0.0"]
```

---

## Test Coverage

- [ ] Load valid configuration file
- [ ] Load configuration with all default values
- [ ] Save configuration creates parent directories
- [ ] Save and reload produces identical config
- [ ] Reject invalid JSON syntax
- [ ] Reject missing required fields
- [ ] Reject invalid field types
- [ ] Handle missing file with FileNotFoundError
- [ ] Enforce UTC timezone on created_at
- [ ] Preserve timezone information on load

---

## Related Capabilities

- Depends on: None (foundational capability)
- Used by: `backend-registry`, `service-factory`, `project-management`
