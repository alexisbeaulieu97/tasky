# service-factory Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
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

