# Capability: Backend Registry

**Status**: Draft  
**Capability ID**: `backend-registry`  
**Package**: `tasky-settings`

---

## ADDED Requirements

### Requirement: Backend factory registration

The system SHALL provide a registry where storage backends can register factory functions that create repository instances.

#### Scenario: Register a backend factory

```gherkin
Given a BackendRegistry instance
And a factory function: factory(path: Path) -> TaskRepository
When I call registry.register("json", factory)
Then the backend "json" is registered
And calling registry.get("json") returns the factory function
```

#### Scenario: Register multiple backends

```gherkin
Given a BackendRegistry instance
And factory functions for "json", "sqlite", and "postgres"
When I register all three backends
Then registry.list_backends() returns ["json", "postgres", "sqlite"]
And each backend can be retrieved via registry.get(name)
```

#### Scenario: Overwrite existing backend

```gherkin
Given a BackendRegistry with "json" backend registered
When I call registry.register("json", new_factory)
Then the old factory is replaced
And registry.get("json") returns new_factory
```

---

### Requirement: Backend retrieval with validation

The system SHALL validate backend names during retrieval and raise descriptive errors for unregistered backends.

#### Scenario: Retrieve registered backend

```gherkin
Given a BackendRegistry with "json" backend registered
When I call registry.get("json")
Then it returns the registered factory function
```

#### Scenario: Attempt to retrieve unregistered backend

```gherkin
Given a BackendRegistry with only "json" registered
When I call registry.get("postgres")
Then it raises KeyError
And the error message includes "postgres"
And the error message lists available backends: ["json"]
```

---

### Requirement: Global registry singleton

The system SHALL provide a global singleton registry instance for convenient backend registration.

#### Scenario: Use global registry

```gherkin
Given the global registry is imported from tasky_settings
When a backend imports and calls registry.register("json", factory)
Then the registration is visible to all modules using the global registry
And calling registry.get("json") returns the factory
```

#### Scenario: Multiple modules can register to the same registry

```gherkin
Given module A registers backend "json"
And module B registers backend "sqlite"
When module C calls registry.list_backends()
Then it returns ["json", "sqlite"]
```

---

### Requirement: Type-safe factory protocol

The system SHALL define a `BackendFactory` protocol ensuring factories accept a Path and return TaskRepository.

#### Scenario: Valid factory signature

```gherkin
Given a function with signature: factory(path: Path) -> TaskRepository
When I register it with registry.register("json", factory)
Then the registration succeeds
And type checkers report no errors
```

#### Scenario: Invalid factory signature detected by type checker

```gherkin
Given a function with signature: factory(path: str) -> dict
When I attempt to register it (in type-checked code)
Then the type checker reports a type mismatch
```

---

### Requirement: Backend listing for diagnostics

The system SHALL provide a method to list all registered backend names.

#### Scenario: List backends when none registered

```gherkin
Given a new BackendRegistry instance
When I call registry.list_backends()
Then it returns an empty list []
```

#### Scenario: List backends in sorted order

```gherkin
Given backends "sqlite", "json", "postgres" are registered
When I call registry.list_backends()
Then it returns ["json", "postgres", "sqlite"]
```

---

## Implementation Notes

### Package Structure

```
packages/tasky-settings/
├── src/tasky_settings/
│   ├── __init__.py                 # Exports registry, BackendFactory, etc.
│   └── backend_registry.py         # BackendRegistry class
├── tests/
│   └── test_registry.py            # Registry tests
└── pyproject.toml
```

### Key Classes

```python
from pathlib import Path
from typing import Callable

from tasky_tasks.ports import TaskRepository

BackendFactory = Callable[[Path], TaskRepository]

class BackendRegistry:
    """Registry for storage backend factories."""
    
    def __init__(self) -> None:
        self._backends: dict[str, BackendFactory] = {}
    
    def register(self, name: str, factory: BackendFactory) -> None:
        """Register a backend factory."""
        self._backends[name] = factory
    
    def get(self, name: str) -> BackendFactory:
        """Get a registered backend factory."""
        if name not in self._backends:
            available = sorted(self._backends.keys())
            raise KeyError(
                f"Backend '{name}' not found. Available: {available}"
            )
        return self._backends[name]
    
    def list_backends(self) -> list[str]:
        """List all registered backend names."""
        return sorted(self._backends.keys())

# Global singleton
registry = BackendRegistry()
```

### Dependencies

```toml
[project]
name = "tasky-settings"
requires-python = ">=3.13"
dependencies = ["tasky-tasks"]  # For TaskRepository protocol
```

---

## Test Coverage

- [ ] Register a backend and retrieve it
- [ ] Register multiple backends
- [ ] Overwrite existing backend
- [ ] Retrieve unregistered backend raises KeyError with helpful message
- [ ] List backends returns empty list when none registered
- [ ] List backends returns sorted names
- [ ] Global registry is accessible from multiple modules
- [ ] Type checker validates BackendFactory signature

---

## Related Capabilities

- Depends on: `task-repository-protocol` (from `tasky-tasks`)
- Used by: `service-factory`, `backend-self-registration`
- Related to: `project-configuration` (registry uses config to select backend)
