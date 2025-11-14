# Tasky Architecture Documentation

## Backend Registration Pattern

### Overview

Tasky uses a **self-registration pattern** for storage backends. This design keeps the settings layer generic and extensible without coupling it to specific backend implementations.

### How It Works

1. **Backend Implementation** (`tasky-storage`)
   - Each backend (JSON, SQLite, etc.) lives in `packages/tasky-storage/backends/<name>/`
   - Backend registers itself at import time:
     ```python
     # In tasky_storage/backends/json/__init__.py
     try:
         from tasky_settings import registry
         registry.register("json", JsonTaskRepository.from_path)
     except ImportError:
         pass  # tasky-settings not installed (e.g., during dev)
     ```

2. **Factory Initialization** (`tasky-settings`)
   - `create_task_service()` calls `_ensure_backends_registered()`
   - This triggers import of `tasky_storage`, which imports modules listed in `tasky_storage/__init__.py`
   - Only the modules explicitly imported are executed, so new backends must be reachable via package import
   - Pattern is thread-safe (uses lock) and idempotent (runs once)

3. **Registry Lookup**
   - Once initialized, `registry.get(backend_name)` returns the factory function
   - Factory creates repository instance: `repository = factory(storage_path)`

### Why This Design?

#### ✓ Benefits

- **Settings stays generic**: No backend-specific code in `tasky_settings`
- **Extensible without core changes**: Add new backends (PostgreSQL, DuckDB, etc.) without modifying settings
- **Third-party backends possible**: External packages can register themselves
- **Decoupled implementation**: New backends only require changes in `tasky_storage`
- **Works in isolation**: Tests can import factory without triggering all backends

#### ✗ Alternatives Rejected

**Explicit Registration in Settings**
```python
# ❌ Don't do this
def _register_backends():
    from tasky_storage.backends.json import json_factory
    from tasky_storage.backends.sqlite import sqlite_factory
    registry.register("json", json_factory)
    registry.register("sqlite", sqlite_factory)
```

Problems:
- Couples `tasky_settings` to every backend
- Requires editing settings for each new backend
- Breaks third-party backend extensibility
- Makes settings a dependency hub instead of configuration layer

### Adding a New Backend

To add a new backend (e.g., PostgreSQL):

1. Create `packages/tasky-storage/backends/postgres/` directory
2. Implement `PostgresTaskRepository` class with `from_path()` factory method
3. Add registration in `backends/postgres/__init__.py`:
   ```python
   try:
       from tasky_settings import registry
       registry.register("postgres", PostgresTaskRepository.from_path)
   except ImportError:
       pass
   ```
4. Update `packages/tasky-storage/__init__.py` to import the backend module:
   ```python
   # This import triggers the backend's self-registration
   from tasky_storage.backends import postgres  # noqa: F401
   ```
5. **No changes needed in tasky_settings**

**Important**: New backends must be imported in `packages/tasky-storage/__init__.py` to be discoverable. This is a one-time setup cost that keeps the self-registration pattern decoupled from settings.

### Testing the Pattern

The subprocess isolation test in **`packages/tasky-settings/tests/test_factory_isolation.py`** verifies:
- Factory works when only `tasky_settings` is imported
- Backends are initialized automatically on first use
- Multiple calls don't re-import or cause errors
- No explicit `tasky_storage` import required by caller

```python
def test_factory_works_without_explicit_storage_import():
    """Factory initializes backends automatically (proven by subprocess isolation)"""
```

This test runs in a subprocess with only `tasky_settings` imported, proving that lazy initialization of backends works correctly without explicit imports by the caller.

### Thread Safety

The pattern ensures thread-safe operation across two layers:

**Registry Initialization** (`tasky-settings`)
- Global lock (`_init_lock`) protects the single initialization
- Boolean flag prevents re-initialization after first call
- Multiple threads calling `create_task_service()` simultaneously will block until initialization completes

**Backend-Specific Concurrency** (`tasky-storage`)
- Each backend implements its own thread-safety guarantees independently
- SQLite backend uses per-database-file connection pooling with locks
- This separation keeps registry initialization concerns distinct from backend concurrency

Multi-threaded environments (e.g., MCP servers) can safely call `create_task_service()` concurrently without coordination.

### Third-Party Backends (Out-of-Tree Extensions)

The self-registration pattern enables external packages to provide backends without modifying tasky:

**To create an out-of-tree backend** (e.g., `my-org/tasky-postgres`):

1. Implement `PostgresTaskRepository` in your package (must implement `TaskRepository` protocol)
2. Add registration in your package's `__init__.py`:
   ```python
   try:
       from tasky_settings import registry
       from .postgres_repository import PostgresTaskRepository
       registry.register("postgres", PostgresTaskRepository.from_path)
   except ImportError:
       pass  # tasky-settings not available in isolated test environment
   ```
3. Document that users must install your package alongside tasky
4. Users then include your package in their environment:
   ```bash
   pip install tasky my-org-tasky-postgres
   ```
5. When tasky initializes backends, your package's module is imported automatically (if installed)

**Key contract for third-party backends**:
- Must be installed in the same environment as tasky
- Must implement the `TaskRepository` protocol (duck typing)
- Must register with the global registry at module scope
- Should handle `ImportError` gracefully if `tasky_settings` is unavailable

This enables ecosystems where specialized backends (cloud storage, graph databases, etc.) are maintained separately and remain optional.

### Relationship to Clean Architecture

This pattern maintains the clean architecture:

```
Domain (tasky_tasks)
  ↑
Service Layer (tasky_settings)
  ↑
Storage Adapters (tasky_storage/backends/*)
  ↑
Registry (tasky_settings)
```

- **Domain** exports protocols (`TaskRepository`)
- **Service** (settings) orchestrates without knowing backends
- **Adapters** implement protocols and self-register
- **Registry** discovers registered backends on demand
- **Caller** doesn't need to know about backends

No layer has unnecessary coupling to implementation details.

---

## Related Patterns

- **Backend Registry**: Central registry of available backends
- **Factory Pattern**: `SqliteTaskRepository.from_path()` creates instances
- **Self-Registration**: Backends register themselves at import time
- **Lazy Initialization**: Backends only imported when factory is first used
