# Capability: Service Factory

**Status**: Draft
**Capability ID**: `task-service-factory`
**Package**: `tasky-settings`

---

## ADDED Requirements

### Requirement: Task service factory from configuration

The system SHALL provide a factory function that creates a fully configured TaskService by reading project configuration and using the backend registry.

#### Scenario: Create service from explicit project root

```gherkin
Given a project root at "/home/user/myproject"
And a config file at "/home/user/myproject/.tasky/config.toml" with:
  """
  [storage]
  backend = "json"
  path = "tasks.json"
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
And a config file at ".tasky/config.toml" with backend "json"
And the "json" backend is registered
When I call create_task_service() with no arguments
Then it returns a TaskService using the current directory as project root
And the repository points to "/home/user/myproject/.tasky/tasks.json"
```

#### Scenario: Walk up directory tree to find project root

```gherkin
Given the current directory is "/home/user/myproject/src/components"
And a ".tasky" directory at "/home/user/myproject/.tasky"
When I call create_task_service() with no arguments
Then it walks up the directory tree
And finds the ".tasky" directory at "/home/user/myproject/.tasky"
And creates a service rooted at "/home/user/myproject"
```

---

### Requirement: Project root discovery

The system SHALL provide a function to find the project root by searching for the `.tasky/` directory.

#### Scenario: Find project root in current directory

```gherkin
Given the current directory contains a ".tasky" subdirectory
When I call find_project_root()
Then it returns the current directory path
```

#### Scenario: Find project root in parent directory

```gherkin
Given the current directory is "/home/user/myproject/nested/deep"
And "/home/user/myproject/.tasky" exists
When I call find_project_root()
Then it returns "/home/user/myproject"
```

#### Scenario: Find project root from explicit start path

```gherkin
Given a project root at "/home/user/myproject"
And start path at "/home/user/myproject/src"
When I call find_project_root(start_path=Path("/home/user/myproject/src"))
Then it returns "/home/user/myproject"
```

---

### Requirement: Missing project error handling

The system SHALL raise a descriptive error when no project is found.

#### Scenario: No .tasky directory found

```gherkin
Given the current directory is "/home/user/no-project"
And no ".tasky" exists in this directory or any parent
When I call create_task_service()
Then it raises ProjectNotFoundError
And the error message includes "No project found"
And the error message suggests running "tasky project init"
```

#### Scenario: ProjectNotFoundError with start path

```gherkin
Given ProjectNotFoundError is raised
When I access exc_info.value.start_path
Then it contains the path where the search started
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

#### Scenario: Empty backend name handled by validation

```gherkin
Given a config file with backend ""
When I call create_task_service()
Then it raises KeyError
And the error message indicates the backend name is not available
```

---

### Requirement: Absolute path construction

The system SHALL construct absolute paths for storage files relative to the project root's `.tasky/` directory.

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

#### Scenario: Repository initialization

```gherkin
Given a backend factory is called
When the factory creates a repository
Then the repository's initialize() method is called
And the repository is ready to use
```

---

### Requirement: Configuration hierarchy respect

The system SHALL respect the hierarchical configuration system when loading storage settings.

#### Scenario: Environment variable overrides config file

```gherkin
Given a config file with backend="json"
And environment variable TASKY_STORAGE_BACKEND="sqlite"
When I call create_task_service()
Then the service uses "sqlite" backend
And ignores the "json" value in config file
```

#### Scenario: CLI overrides take precedence

```gherkin
Given a config file with backend="json"
When I call get_settings(cli_overrides={"storage": {"backend": "sqlite"}})
Then settings.storage.backend == "sqlite"
```

---

## Implementation Notes

### Package Structure

```
packages/tasky-settings/
├── src/tasky_settings/
│   ├── __init__.py                 # Exports create_task_service, find_project_root, etc.
│   ├── factory.py                  # Project discovery and service factory functions
│   └── backend_registry.py         # BackendRegistry
├── tests/
│   └── test_factory.py             # Factory and discovery tests
└── pyproject.toml
```

### Key Functions

```python
from pathlib import Path

from tasky_settings.backend_registry import registry
from tasky_tasks.service import TaskService


class ProjectNotFoundError(Exception):
    """Raised when no project configuration is found."""

    def __init__(self, start_path: Path) -> None:
        super().__init__(
            f"No project found. Searched from {start_path} up to root. "
            "Run 'tasky project init' to create a project."
        )
        self.start_path = start_path


def find_project_root(start_path: Path | None = None) -> Path:
    """Find project root by walking up directory tree.

    Searches for a .tasky directory starting from start_path
    and walking up to parent directories.

    Args:
        start_path: Starting path for search, defaults to current directory

    Returns:
        Path to project root (parent of .tasky directory)

    Raises:
        ProjectNotFoundError: If no .tasky directory found
    """
    current = start_path or Path.cwd()
    current = current.resolve()

    for path in [current, *current.parents]:
        tasky_dir = path / ".tasky"
        if tasky_dir.is_dir():
            return path

    raise ProjectNotFoundError(current)


def create_task_service(project_root: Path | None = None) -> TaskService:
    """Create a TaskService from project configuration.

    Loads settings from .tasky/config.toml and instantiates the appropriate
    storage backend using the backend registry.

    Args:
        project_root: Explicit project root, or None to auto-detect

    Returns:
        Fully configured TaskService instance

    Raises:
        ProjectNotFoundError: If no project directory found
        KeyError: If configured backend is not registered
    """
    # Avoid circular import by importing locally
    from tasky_settings import get_settings as _get_settings  # noqa: PLC0415

    # Find project root if not provided
    if project_root is None:
        project_root = find_project_root()
    else:
        # If project_root is provided, verify it exists
        project_root = project_root.resolve()
        tasky_dir = project_root / ".tasky"
        if not tasky_dir.is_dir():
            raise ProjectNotFoundError(project_root)

    # Load settings with project root context
    settings = _get_settings(project_root=project_root)

    # Get backend factory
    factory = registry.get(settings.storage.backend)

    # Construct absolute storage path
    storage_path = project_root / ".tasky" / settings.storage.path

    # Create repository
    repository = factory(storage_path)

    # Initialize storage
    repository.initialize()

    # Return configured service
    return TaskService(repository=repository)
```

### Dependencies

```toml
[project]
name = "tasky-settings"
requires-python = ">=3.13"
dependencies = [
    "tasky-tasks",              # For TaskService, TaskRepository
    "pydantic",                 # For AppSettings model
    "pydantic-settings",        # For hierarchical configuration
]
```

---

## Test Coverage

- [ ] Find project root in current directory with .tasky
- [ ] Find project root by walking up directory tree
- [ ] Find project root from explicit start path
- [ ] find_project_root() defaults to current working directory
- [ ] ProjectNotFoundError includes start_path attribute
- [ ] Create service with explicit project root
- [ ] Create service from current directory (auto-discovery)
- [ ] Raise ProjectNotFoundError when project_root provided but invalid
- [ ] Raise ProjectNotFoundError when no project found
- [ ] Raise KeyError for unregistered backend
- [ ] Construct absolute path for relative storage.path
- [ ] Handle storage.path with subdirectories
- [ ] Invoke backend factory with correct absolute path
- [ ] Return TaskService with configured repository
- [ ] Call repository.initialize() after creation
- [ ] Respect environment variable overrides
- [ ] Respect CLI overrides in get_settings()

---

## Related Capabilities

- Depends on: `storage-configuration`, `backend-registry`
- Used by: `task-cli-operations`, `project-cli-operations`
- Related to: `backend-self-registration` (ensures backends are available)
