# Capability: Service Factory

**Status**: Draft  
**Capability ID**: `service-factory`  
**Package**: `tasky-settings`

---

## ADDED Requirements

### Requirement: Task service factory from configuration

The system SHALL provide a factory function that creates a fully configured TaskService by reading project configuration and using the backend registry.

#### Scenario: Create service from explicit project root

```gherkin
Given a project root at "/home/user/myproject"
And a config file at "/home/user/myproject/.tasky/config.json" with:
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
And the "json" backend is registered in the registry
When I call create_task_service(Path("/home/user/myproject"))
Then it returns a TaskService instance
And the service uses a JsonTaskRepository
And the repository points to "/home/user/myproject/.tasky/tasks.json"
```

#### Scenario: Create service from current directory

```gherkin
Given the current directory is "/home/user/myproject"
And a config file at ".tasky/config.json" with backend "json"
And the "json" backend is registered
When I call create_task_service() with no arguments
Then it returns a TaskService using the current directory as project root
And the repository points to "/home/user/myproject/.tasky/tasks.json"
```

#### Scenario: Walk up directory tree to find project root

```gherkin
Given the current directory is "/home/user/myproject/src/components"
And a config file at "/home/user/myproject/.tasky/config.json"
When I call create_task_service() with no arguments
Then it walks up the directory tree
And finds the config at "/home/user/myproject/.tasky/config.json"
And creates a service rooted at "/home/user/myproject"
```

---

### Requirement: Missing project error handling

The system SHALL raise a descriptive error when no project configuration is found.

#### Scenario: No config file in current directory or parents

```gherkin
Given the current directory is "/home/user/no-project"
And no ".tasky/config.json" exists in this directory or any parent
When I call create_task_service()
Then it raises ProjectNotFoundError
And the error message includes "No .tasky/config.json found"
And the error message suggests running "tasky project init"
```

#### Scenario: Config directory exists but no config file

```gherkin
Given a directory ".tasky" exists
But no file ".tasky/config.json" exists
When I call create_task_service()
Then it raises ProjectNotFoundError
```

---

### Requirement: Backend validation

The system SHALL validate that the configured backend is registered and raise a descriptive error for invalid backends.

#### Scenario: Invalid backend in configuration

```gherkin
Given a config file with backend "postgres"
But only "json" and "sqlite" are registered
When I call create_task_service()
Then it raises KeyError
And the error message includes "Backend 'postgres' not found"
And the error message lists available backends: ["json", "sqlite"]
```

#### Scenario: Empty backend name

```gherkin
Given a config file with backend ""
When I call create_task_service()
Then it raises KeyError
And the error message indicates invalid backend name
```

---

### Requirement: Absolute path construction

The system SHALL construct absolute paths for storage files relative to the project root.

#### Scenario: Relative storage path in config

```gherkin
Given project root is "/home/user/myproject"
And config specifies storage.path = "tasks.json"
When I call create_task_service()
Then the repository uses absolute path "/home/user/myproject/.tasky/tasks.json"
```

#### Scenario: Storage path with subdirectory

```gherkin
Given project root is "/home/user/myproject"
And config specifies storage.path = "data/tasks.db"
When I call create_task_service()
Then the repository uses absolute path "/home/user/myproject/.tasky/data/tasks.db"
```

---

### Requirement: Factory invocation with correct parameters

The system SHALL invoke the backend factory with the correct storage path.

#### Scenario: Factory receives absolute path

```gherkin
Given a mock backend factory registered as "json"
And config specifies backend "json" and path "tasks.json"
When I call create_task_service()
Then the factory is called with Path("/project/root/.tasky/tasks.json")
And the factory returns a TaskRepository instance
And that repository is passed to TaskService constructor
```

---

## Implementation Notes

### Package Structure

```
packages/tasky-settings/
├── src/tasky_settings/
│   ├── __init__.py                 # Exports create_task_service, etc.
│   ├── backend_registry.py         # BackendRegistry
│   └── factory.py                  # create_task_service function
├── tests/
│   └── test_factory.py             # Factory tests
└── pyproject.toml
```

### Key Functions

```python
from pathlib import Path

from tasky_projects import ProjectConfig
from tasky_settings.backend_registry import registry
from tasky_tasks.service import TaskService


class ProjectNotFoundError(Exception):
    """Raised when no project configuration is found."""
    pass


def find_project_root(start_path: Path | None = None) -> Path:
    """Find project root by walking up directory tree."""
    current = start_path or Path.cwd()
    for parent in [current, *current.parents]:
        config_path = parent / ".tasky" / "config.json"
        if config_path.exists():
            return parent
    raise ProjectNotFoundError(
        "No .tasky/config.json found. Run 'tasky project init' first."
    )


def create_task_service(project_root: Path | None = None) -> TaskService:
    """Create a TaskService from project configuration.
    
    Args:
        project_root: Explicit project root, or None to auto-detect
        
    Returns:
        Fully configured TaskService instance
        
    Raises:
        ProjectNotFoundError: If no config found
        KeyError: If configured backend is not registered
    """
    if project_root is None:
        project_root = find_project_root()
    
    config_path = project_root / ".tasky" / "config.json"
    config = ProjectConfig.from_file(config_path)
    
    # Get backend factory from registry
    factory = registry.get(config.storage.backend)
    
    # Construct absolute storage path
    storage_path = project_root / ".tasky" / config.storage.path
    
    # Create repository and service
    repository = factory(storage_path)
    return TaskService(repository=repository)
```

### Dependencies

```toml
[project]
name = "tasky-settings"
requires-python = ">=3.13"
dependencies = [
    "tasky-tasks",      # For TaskService, TaskRepository
    "tasky-projects",   # For ProjectConfig
]
```

---

## Test Coverage

- [ ] Create service with explicit project root
- [ ] Create service from current directory
- [ ] Walk up directory tree to find project root
- [ ] Raise ProjectNotFoundError when no config found
- [ ] Raise ProjectNotFoundError when .tasky exists but config missing
- [ ] Raise KeyError for unregistered backend
- [ ] Construct absolute path for relative storage.path
- [ ] Handle storage.path with subdirectories
- [ ] Invoke backend factory with correct absolute path
- [ ] Return TaskService with configured repository

---

## Related Capabilities

- Depends on: `project-configuration`, `backend-registry`, `task-repository-protocol`
- Used by: `task-cli-operations`, `project-cli-operations`
- Related to: `backend-self-registration` (ensures backends are available)
