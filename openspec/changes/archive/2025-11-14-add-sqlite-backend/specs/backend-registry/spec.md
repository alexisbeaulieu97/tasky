## MODIFIED Requirements

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
