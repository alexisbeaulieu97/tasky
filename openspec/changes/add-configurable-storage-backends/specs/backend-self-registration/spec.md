# Capability: Backend Self-Registration

**Status**: Draft  
**Capability ID**: `backend-self-registration`  
**Package**: `tasky-storage`

---

## MODIFIED Requirements

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

## Implementation Notes

### Modified Module Structure

```
packages/tasky-storage/
└── src/tasky_storage/
    ├── __init__.py                      # MODIFIED: Adds registration code
    └── backends/json/
        ├── __init__.py
        ├── repository.py                # MODIFIED: Adds from_path() if missing
        └── ...
```

### Registration Code

```python
# packages/tasky-storage/src/tasky_storage/__init__.py
from .backends.json import JsonStorage, JsonTaskRepository, TaskDocument
from .errors import StorageConfigurationError, StorageDataError, StorageError

# Register backends with the global registry
try:
    from tasky_settings import registry
    registry.register("json", JsonTaskRepository.from_path)
except ImportError:
    # tasky-settings not available (e.g., during isolated testing)
    pass

__all__ = [
    "JsonStorage",
    "JsonTaskRepository",
    "TaskDocument",
    "StorageError",
    "StorageDataError",
    "StorageConfigurationError",
]
```

### Factory Method

```python
# packages/tasky-storage/src/tasky_storage/backends/json/repository.py
from pathlib import Path
from tasky_storage.backends.json.storage import JsonStorage

class JsonTaskRepository:
    """JSON-based task repository implementation."""
    
    @classmethod
    def from_path(cls, path: Path) -> "JsonTaskRepository":
        """Create a repository from a storage path.
        
        This factory method is suitable for backend registry.
        
        Args:
            path: Absolute path to JSON storage file
            
        Returns:
            Configured JsonTaskRepository instance
        """
        storage = JsonStorage(path=path)
        repository = cls(storage=storage)
        repository.initialize()  # Ensure storage file exists
        return repository
```

### Dependencies

No new dependencies—uses existing structure.

---

## Test Coverage

- [ ] Importing tasky_storage registers "json" backend
- [ ] Multiple imports don't cause errors (idempotent)
- [ ] Registration is skipped gracefully when tasky_settings unavailable
- [ ] JsonTaskRepository.from_path creates valid repository
- [ ] from_path initializes storage file if missing
- [ ] Factory method signature matches BackendFactory protocol

---

## Related Capabilities

- Depends on: `backend-registry`
- Used by: `service-factory` (relies on "json" being registered)
- Modifies: Existing `json-storage-backend` capability
