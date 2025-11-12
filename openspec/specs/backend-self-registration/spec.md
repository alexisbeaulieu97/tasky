# backend-self-registration Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
### Requirement: JSON backend self-registration

The JSON storage backend SHALL automatically register itself with the global backend registry upon module import.

#### Scenario: JSON backend registers on import

```gherkin
Given the tasky_settings.registry is available
When I import tasky_storage
Then the "json" backend is registered in the global registry
And registry.get("json") returns JsonTaskRepository.from_path
```

#### Scenario: Registration is idempotent

```gherkin
Given tasky_storage has been imported once
When I import tasky_storage again
Then the "json" backend remains registered
And no errors are raised
```

#### Scenario: Graceful handling when registry unavailable

```gherkin
Given tasky_settings is not installed (testing isolation)
When I import tasky_storage
Then no ImportError is raised
And the backend functions normally (not registered but usable)
```

---

### Requirement: Factory method for backend registration

The JSON repository SHALL provide a factory class method suitable for backend registration.

#### Scenario: Factory creates repository from path

```gherkin
Given a path "/home/user/project/.tasky/tasks.json"
When I call JsonTaskRepository.from_path(path)
Then it returns a JsonTaskRepository instance
And the repository uses a JsonStorage pointing to that path
And the storage file is initialized if it doesn't exist
```

#### Scenario: Factory is compatible with BackendFactory protocol

```gherkin
Given the BackendFactory type requires: Callable[[Path], TaskRepository]
And JsonTaskRepository.from_path has signature: (Path) -> JsonTaskRepository
When I register it with registry.register("json", JsonTaskRepository.from_path)
Then type checkers report no errors
And the registration succeeds at runtime
```

---

