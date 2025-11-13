# Spec Delta: Backend Self-Registration

**Capability**: `backend-self-registration`
**Change**: `ensure-storage-backend-registration`
**Package**: `tasky-storage`, `tasky-settings`
**Layer**: Infrastructure, Configuration

## Overview

This delta updates the backend self-registration specification to document how storage backends are guaranteed to be registered before the service factory uses them. The change clarifies the initialization pattern and adds requirements for automatic backend loading.

---

## ADDED Requirements

### Requirement: Automatic backend registration on factory use

The service factory SHALL ensure storage backends are registered automatically before accessing the registry, without requiring explicit imports from callers.

**Rationale**: Prevents `KeyError` when hosts use `create_task_service()` without separately importing `tasky_storage`. Makes the factory self-contained and eliminates hidden dependencies.

#### Scenario: Factory works without explicit storage import

**Given** a Python module that imports only from `tasky_settings`
**And** the module does NOT import `tasky_storage` anywhere
**When** the module calls `create_task_service(project_root)`
**Then** the function MUST succeed without errors
**And** the configured backend (e.g., "json") MUST be available in the registry
**And** the factory MUST return a working `TaskService` instance

#### Scenario: Backends initialized exactly once

**Given** `create_task_service()` has been called once
**When** `create_task_service()` is called again (multiple times)
**Then** backend registration MUST occur only on the first call
**And** subsequent calls MUST NOT re-import or re-register backends
**And** the registry state MUST remain consistent across calls

#### Scenario: Initialization is transparent to callers

**Given** a caller using `create_task_service()`
**When** the function is called
**Then** the caller MUST NOT need to know about backend registration
**And** the caller MUST NOT need to call initialization functions manually
**And** the factory MUST handle all registration automatically

---

## MODIFIED Requirements

### Requirement: JSON backend self-registration

The JSON storage backend SHALL automatically register itself with the global backend registry upon module import. **The `tasky_settings` factory SHALL ensure this import happens automatically when needed.**

#### Scenario: JSON backend registers on import

**Given** the tasky_settings.registry is available
**When** `tasky_storage` is imported (either explicitly or via factory initialization)
**Then** the "json" backend MUST be registered in the global registry
**And** registry.get("json") MUST return `JsonTaskRepository.from_path`

#### Scenario: Registration is idempotent

**Given** tasky_storage has been imported once
**When** tasky_storage is imported again (or factory initialization runs multiple times)
**Then** the "json" backend MUST remain registered
**And** no errors MUST be raised
**And** the registry state MUST be unchanged

#### Scenario: Graceful handling when registry unavailable

**Given** tasky_settings is not installed (testing isolation)
**When** I import tasky_storage
**Then** no ImportError MUST be raised
**And** the backend MUST function normally (not registered but usable)

---

## ADDED Requirements

### Requirement: Backend initialization pattern documentation

The backend registration initialization pattern MUST be documented clearly for future backend implementers.

**Rationale**: Future backends (SQLite, PostgreSQL) need to follow the same self-registration pattern. Clear documentation prevents mistakes and ensures consistency.

#### Scenario: Registration pattern documented in factory

**Given** a developer reading `tasky_settings/factory.py`
**When** they examine the `_ensure_backends_registered()` function
**Then** the docstring MUST explain why backends are imported
**And** the docstring MUST describe the self-registration pattern
**And** the docstring MUST provide guidance for future backend authors

#### Scenario: Registration pattern documented in storage module

**Given** a developer reading `tasky_storage/__init__.py`
**When** they examine the registration code
**Then** comments MUST explain how backend self-registration works
**And** comments MUST reference the factory's automatic initialization
**And** the pattern MUST be clear enough to serve as a template for new backends

---

## Implementation Notes

### Factory Implementation Pattern

Located in: `packages/tasky-settings/src/tasky_settings/factory.py`

```python
_backends_initialized = False

def _ensure_backends_registered() -> None:
    """Ensure storage backends are registered before using the registry.

    This function imports tasky_storage, which triggers backend self-registration
    via module-level code. It runs once on first call to create_task_service().

    This pattern allows:
    - Service factory to work without requiring explicit tasky_storage import
    - Future backends to follow the same self-registration pattern
    - Tests to use the factory in isolation

    Implementation note:
    Storage adapters register themselves at import time by calling:
        from tasky_settings import registry
        registry.register("backend-name", factory_function)
    """
    global _backends_initialized
    if not _backends_initialized:
        import tasky_storage  # noqa: F401
        _backends_initialized = True


def create_task_service(project_root: Path | None = None) -> TaskService:
    # Ensure backends are available before accessing registry
    _ensure_backends_registered()
    # ... rest of implementation
```

### Storage Module Pattern

Located in: `packages/tasky-storage/src/tasky_storage/__init__.py`

```python
# Register JSON backend with the global registry
# This runs at import time, allowing the backend to be used by the factory.
#
# Backend Registration Pattern:
# - Backends register themselves by importing the registry and calling register()
# - tasky_settings.factory ensures this module is imported before using the registry
# - Future backends should follow this same pattern
try:
    from tasky_settings import registry
    registry.register("json", JsonTaskRepository.from_path)
except ImportError:
    # tasky-settings may not be installed yet (e.g., during development)
    pass
```

---

## Testing Requirements

### Isolation Test

Create: `packages/tasky-settings/tests/test_factory_isolation.py`

- Test that factory works when only `tasky_settings` is imported
- Verify registry contains backends after factory call
- Ensure no `KeyError` occurs
- Use subprocess or import isolation to prove no accidental imports

### Idempotency Test

- Call `create_task_service()` multiple times
- Verify backends registered only once
- Ensure no side effects from repeated calls

### Regression Tests

- Verify all existing tests still pass
- Ensure CLI commands work unchanged
- Confirm no performance impact

---

## Related Specifications

- `backend-registry`: Registry protocol that backends register with
- `service-factory`: Factory function that creates TaskService instances

---

## Migration Notes

No migration required. This is a transparent fix that doesn't change any public APIs or user-facing behavior. Existing code continues to work as-is, with the added benefit that isolated imports now work correctly.
