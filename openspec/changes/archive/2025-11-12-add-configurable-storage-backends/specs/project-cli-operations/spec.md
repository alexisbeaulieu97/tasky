# Capability: Project CLI Operations

**Status**: Draft  
**Capability ID**: `project-cli-operations`  
**Package**: `tasky-cli`

---

## ADDED Requirements

### Requirement: Project initialization with backend selection

The `tasky project init` command SHALL accept a `--backend` option and create a configuration file with the selected backend.

#### Scenario: Initialize project with default backend

```gherkin
Given I am in directory "/home/user/myproject"
And no ".tasky" directory exists
When I run "tasky project init"
Then a directory ".tasky" is created
And a file ".tasky/config.json" is created
And the config contains:
  | field            | value        |
  | version          | "1.0"        |
  | storage.backend  | "json"       |
  | storage.path     | "tasks.json" |
And the config.created_at is the current UTC timestamp
And the CLI outputs "Project initialized in .tasky (backend: json)"
```

#### Scenario: Initialize project with specified backend

```gherkin
Given I am in directory "/home/user/myproject"
When I run "tasky project init --backend sqlite"
Then a config file is created with storage.backend = "sqlite"
And the CLI outputs "Project initialized in .tasky (backend: sqlite)"
```

#### Scenario: Initialize project with short option syntax

```gherkin
Given I am in directory "/home/user/myproject"
When I run "tasky project init -b postgres"
Then a config file is created with storage.backend = "postgres"
```

#### Scenario: Reject invalid backend during init

```gherkin
Given only backends ["json", "sqlite"] are registered
When I run "tasky project init --backend mysql"
Then it exits with error code 1
And the error message includes "Backend 'mysql' not found"
And the error message lists available backends: ["json", "sqlite"]
And no config file is created
```

#### Scenario: Reinitialize existing project

```gherkin
Given a project with ".tasky/config.json" already exists
When I run "tasky project init --backend sqlite"
Then the existing config is overwritten
And a warning is shown: "Overwriting existing configuration"
```

---

## ADDED Requirements

### Requirement: Display project configuration

The system SHALL provide a command to display the current project configuration.

#### Scenario: Show project info

```gherkin
Given a project with config:
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
When I run "tasky project info"
Then the CLI outputs:
  """
  Project Configuration
  ---------------------
  Location: /home/user/myproject/.tasky
  Backend: json
  Storage: tasks.json
  Created: 2025-11-11 10:00:00+00:00
  """
```

#### Scenario: Show info when no project found

```gherkin
Given no ".tasky/config.json" exists
When I run "tasky project info"
Then it exits with error code 1
And the error message includes "No project found"
And the error message suggests "Run 'tasky project init' first"
```

---

### Requirement: Backend validation during init

The system SHALL validate backend availability before creating configuration.

#### Scenario: List available backends in help text

```gherkin
When I run "tasky project init --help"
Then the help text includes:
  """
  --backend, -b TEXT  Storage backend (default: json)
                      Available: json, sqlite
  """
```

#### Scenario: Validate backend is registered

```gherkin
Given only "json" backend is registered
When I run "tasky project init --backend json"
Then the command succeeds
When I run "tasky project init --backend fake"
Then the command fails with "Backend 'fake' not found"
```

---

## Implementation Notes

### Modified Command Structure

```python
# packages/tasky-cli/src/tasky_cli/commands/projects.py
from pathlib import Path

import typer
from tasky_projects import ProjectConfig, StorageConfig
from tasky_settings import registry

project_app = typer.Typer(no_args_is_help=True)


@project_app.command(name="init")
def init_command(
    backend: str = typer.Option(
        "json",
        "--backend",
        "-b",
        help="Storage backend to use",
    ),
) -> None:
    """Initialize a new Tasky project."""
    # Validate backend
    try:
        registry.get(backend)  # Ensure backend exists
    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    
    # Create config
    storage_root = Path(".tasky")
    storage_root.mkdir(parents=True, exist_ok=True)
    
    config = ProjectConfig(
        storage=StorageConfig(
            backend=backend,
            path="tasks.json",  # Could make this configurable too
        )
    )
    
    config_path = storage_root / "config.json"
    if config_path.exists():
        typer.echo("Warning: Overwriting existing configuration", err=True)
    
    config.to_file(config_path)
    
    typer.echo(f"Project initialized in {storage_root} (backend: {backend})")


@project_app.command(name="info")
def info_command() -> None:
    """Show project configuration."""
    try:
        config_path = Path(".tasky/config.json")
        config = ProjectConfig.from_file(config_path)
        
        typer.echo("Project Configuration")
        typer.echo("---------------------")
        typer.echo(f"Location: {config_path.absolute().parent}")
        typer.echo(f"Backend: {config.storage.backend}")
        typer.echo(f"Storage: {config.storage.path}")
        typer.echo(f"Created: {config.created_at}")
    except FileNotFoundError:
        typer.echo("Error: No project found", err=True)
        typer.echo("Run 'tasky project init' first", err=True)
        raise typer.Exit(1)
```

### Dependencies

```toml
[project]
name = "tasky-cli"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.20.0",
    "tasky-settings",   # For registry
    "tasky-projects",   # For ProjectConfig
]
```

---

## Test Coverage

- [ ] Init with default backend creates valid config
- [ ] Init with --backend option uses specified backend
- [ ] Init with -b short option works
- [ ] Init with invalid backend shows error and available backends
- [ ] Init overwrites existing config with warning
- [ ] Info displays configuration correctly
- [ ] Info shows error when no project found
- [ ] Help text lists available backends

---

## Related Capabilities

- Depends on: `project-configuration`, `backend-registry`
- Modifies: Existing `project-management` capability
- Used by: Users setting up new projects
