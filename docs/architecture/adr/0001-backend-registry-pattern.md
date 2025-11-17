# ADR-001: Backend Registry Pattern with Self-Registration

## Status
Accepted

## Context
The system needs to support multiple storage backends (JSON, SQLite, PostgreSQL, etc.) without tight coupling between the domain layer and infrastructure implementations. The configuration layer must be able to discover and instantiate backends dynamically based on user settings without importing every backend module explicitly.

Early implementations created circular dependencies where the settings factory needed to import all backends, which in turn imported domain types. This led to initialization order issues and made adding new backends require changes to the factory code.

## Decision
We implement a **backend registry pattern with self-registration** where:

1. Each storage backend registers itself with a global `BackendRegistry` on module import
2. The registry maps backend type strings (e.g., "json", "sqlite") to factory functions
3. The settings factory calls `create_task_service(backend_type)` which looks up the appropriate backend from the registry
4. Backend modules use the `@backend_registry.register("backend_name")` decorator pattern to self-register their factory functions

**Implementation:**
```python
# In tasky-storage/__init__.py
backend_registry = BackendRegistry()

# In tasky-storage/backends/json.py
@backend_registry.register("json")
def create_json_repository(config) -> TaskRepository:
    return JSONTaskRepository(config.data_path)

# In tasky-settings/factory.py
def create_task_service(config: StorageConfig) -> TaskService:
    factory = backend_registry.get_backend(config.backend_type)
    repository = factory(config)
    return TaskService(repository)
```

## Consequences

### Positive
- **Zero coupling**: Settings factory doesn't import any backend modules directly
- **Easy extensibility**: Adding a new backend requires only creating the module and decorating the factory function
- **No initialization order issues**: Backends register themselves when imported, but the factory doesn't force imports
- **Clear contracts**: The repository protocol defines the interface, backends implement it
- **Testable**: Can inject mock backends for testing without modifying registry

### Negative
- **Magic imports**: Backends must be imported somewhere for registration to happen (handled in `tasky_storage/__init__.py`)
- **Runtime errors**: Invalid backend types fail at runtime rather than import time (acceptable trade-off)
- **Global state**: The registry is a global singleton (but this is acceptable for configuration-time setup)

## Alternatives Considered

### Alternative 1: Explicit Factory Methods
Create explicit factory methods for each backend in the settings module:
```python
def create_json_task_service(config): ...
def create_sqlite_task_service(config): ...
```

**Rejected because:**
- Requires settings to import all backend modules, creating coupling
- Every new backend requires modifying the settings module
- Doesn't scale as we add more backends

### Alternative 2: Plugin Discovery with Entry Points
Use Python entry points for backend discovery:
```toml
[project.entry-points."tasky.backends"]
json = "tasky_storage.backends.json:JSONBackend"
```

**Rejected because:**
- Over-engineered for a monorepo workspace
- Adds setup.py/pyproject.toml complexity
- Better suited for true plugin architectures with separate distribution
- Self-registration is simpler and sufficient for our needs

### Alternative 3: Dependency Injection Container
Use a full DI container (e.g., `dependency-injector`, `injector`):

**Rejected because:**
- Adds external dependency for a simple problem
- Learning curve for contributors
- Registry pattern is lightweight and sufficient

## References
- `packages/tasky-storage/src/tasky_storage/registry.py` - Registry implementation
- `packages/tasky-settings/src/tasky_settings/factory.py` - Factory usage
