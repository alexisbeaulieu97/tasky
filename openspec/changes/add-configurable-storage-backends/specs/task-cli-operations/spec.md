# Capability: Task CLI Operations

**Status**: Draft  
**Capability ID**: `task-cli-operations`  
**Package**: `tasky-cli`

---

## MODIFIED Requirements

### Requirement: Task commands use service factory

All task CLI commands SHALL use `create_task_service()` instead of directly instantiating repositories.

#### Scenario: List tasks using factory

```gherkin
Given a project with config specifying backend "json"
And the project contains 2 tasks
When I run "tasky task list"
Then the command calls create_task_service()
And the service uses the configured backend
And both tasks are displayed
```

#### Scenario: Create task using factory

```gherkin
Given a project with config specifying backend "json"
When I run 'tasky task create "Buy milk" "From the store"'
Then the command calls create_task_service()
And a new task is created via the configured backend
And the CLI outputs "Task created: Buy milk"
```

---

### Requirement: Error handling for missing project

Task commands SHALL provide helpful error messages when no project is initialized.

#### Scenario: List tasks without project initialization

```gherkin
Given no ".tasky/config.json" exists in current directory or parents
When I run "tasky task list"
Then it exits with error code 1
And the error message includes "No project found"
And the error message includes "Run 'tasky project init' first"
```

#### Scenario: Create task without project initialization

```gherkin
Given no project is initialized
When I run 'tasky task create "Task" "Details"'
Then it exits with error code 1
And the error message suggests running "tasky project init"
```

---

### Requirement: Transparent backend selection

Task commands SHALL work with any registered backend without code changes.

#### Scenario: List tasks with SQLite backend

```gherkin
Given a project with config specifying backend "sqlite"
And the "sqlite" backend is registered
When I run "tasky task list"
Then the command uses SqliteTaskRepository
And tasks are retrieved from the SQLite database
And tasks are displayed correctly
```

#### Scenario: List tasks with JSON backend

```gherkin
Given a project with config specifying backend "json"
When I run "tasky task list"
Then the command uses JsonTaskRepository
And tasks are retrieved from the JSON file
```

---

### Requirement: Backend configuration errors

Task commands SHALL handle backend configuration errors gracefully.

#### Scenario: Configured backend not registered

```gherkin
Given a config file specifying backend "postgres"
But no "postgres" backend is registered
When I run "tasky task list"
Then it exits with error code 1
And the error message includes "Backend 'postgres' not found"
And the error message lists available backends
```

---

## Implementation Notes

### Modified Command Structure

```python
# packages/tasky-cli/src/tasky_cli/commands/tasks.py
import typer
from tasky_settings import ProjectNotFoundError, create_task_service

task_app = typer.Typer(no_args_is_help=True)


def get_service():
    """Helper to get TaskService with error handling."""
    try:
        return create_task_service()
    except ProjectNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("Run 'tasky project init' first", err=True)
        raise typer.Exit(1)
    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@task_app.command(name="list")
def list_command() -> None:
    """List all tasks."""
    service = get_service()
    tasks = service.get_all_tasks()
    
    if not tasks:
        typer.echo("No tasks found")
        return
    
    for task in tasks:
        typer.echo(f"{task.name} - {task.details}")


@task_app.command(name="create")
def create_command(
    name: str = typer.Argument(..., help="Task name"),
    details: str = typer.Argument(..., help="Task details"),
) -> None:
    """Create a new task."""
    service = get_service()
    task = service.create_task(name=name, details=details)
    typer.echo(f"Task created: {task.name}")
```

### Removed Code

Remove all direct imports and usage of:
- `JsonTaskRepository`
- `JsonStorage`
- Hardcoded paths like `Path(".tasky/tasks.json")`

### Dependencies

```toml
[project]
name = "tasky-cli"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.20.0",
    "tasky-settings",   # For create_task_service
    # Remove direct dependency on tasky-storage
]
```

---

## Test Coverage

- [ ] List tasks uses create_task_service()
- [ ] Create task uses create_task_service()
- [ ] List without project shows helpful error
- [ ] Create without project shows helpful error
- [ ] Commands work with JSON backend
- [ ] Commands work with SQLite backend (when available)
- [ ] Invalid backend in config shows error
- [ ] Unregistered backend shows available options

---

## Related Capabilities

- Depends on: `service-factory`, `project-configuration`
- Modifies: All existing task command implementations
- Related to: `backend-self-registration` (ensures backends available)
