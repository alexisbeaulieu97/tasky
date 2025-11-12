# task-cli-operations Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
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

