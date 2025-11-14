# Proposal: Ensure Storage Backend Registration

**Change ID**: `ensure-storage-backend-registration`
**Status**: Draft
**Phase**: 1.5 (Pre-SQLite Fix)
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal fixes a critical hidden dependency issue where `create_task_service()` fails with `KeyError` when hosts import from `tasky_settings` without explicitly importing `tasky_storage`. The backend registry relies on import-time side effects for registration, but `tasky_settings` doesn't guarantee storage modules are loaded before the registry is accessed.

## Problem Statement

The current implementation has a hidden dependency chain:

1. `tasky_settings.factory.create_task_service()` calls `registry.get(backend_name)`
2. The registry is only populated when `tasky_storage` is imported
3. `tasky_storage.__init__.py` registers backends via import-time side effect
4. **But** `tasky_settings` doesn't import `tasky_storage` anywhere
5. **Result**: Any host that imports `create_task_service` without separately importing `tasky_storage` gets `KeyError: Backend 'json' not registered`

This affects:
- MCP servers that might only import from `tasky_settings`
- Future hosts or tools that use the service factory
- Tests that import the factory in isolation

The error message is confusing because it suggests the backend isn't registered, when the real issue is that the storage module was never imported to trigger registration.

## What Changes

- Add `_ensure_backends_registered()` helper function in `tasky_settings/factory.py`
- Call the helper at the start of `create_task_service()` to trigger backend imports
- Update documentation in `tasky_storage/__init__.py` to explain the registration pattern
- Add isolation test proving factory works without explicit `tasky_storage` import
- Update `create_task_service()` docstring to reflect automatic backend initialization

## Impact

- **Affected specs**: `backend-self-registration`, `service-factory`
- **Affected code**:
  - `packages/tasky-settings/src/tasky_settings/factory.py` (add initialization helper)
  - `packages/tasky-storage/src/tasky_storage/__init__.py` (update comments)
  - `packages/tasky-settings/tests/test_factory_isolation.py` (new test file)
- **Breaking changes**: None - purely additive fix
- **User impact**: None - transparent fix for internal dependency issue
- **Performance**: Negligible (one-time import on first factory use)

## Why

This is a Phase 1.5 fix (before adding SQLite in Phase 2) because:

1. **Critical Bug**: The service factory is fundamentally broken for any host except the CLI (which happens to import tasky_storage)
2. **Blocks Phase 2**: SQLite backend will have the same registration pattern, so fixing this now prevents doubling the problem
3. **Quick Fix**: ~0.5 hours to implement and test
4. **Improves Developer Experience**: Makes the factory "just work" without requiring callers to understand import-time registration

Without this fix, every new backend we add inherits the same fragility, and every new host must discover and work around the hidden dependency.

## Proposed Solution

**Option C** (Recommended): Ensure backends are registered automatically when `create_task_service()` is first called.

Add an eager initialization function in `tasky_settings/factory.py` that imports `tasky_storage` to trigger backend registration:

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
        # Import triggers backend registration via tasky_storage.__init__.py
        import tasky_storage  # noqa: F401
        _backends_initialized = True


def create_task_service(project_root: Path | None = None) -> TaskService:
    """Create a TaskService instance from project configuration.

    ... existing docstring ...
    """
    # Ensure backends are available before accessing registry
    _ensure_backends_registered()

    # ... rest of existing implementation ...
```

**Why Option C over A or B:**
- **vs Option A** (import in `__init__.py`): Keeps import side effects localized to where they're needed rather than at module load time
- **vs Option B** (separate function): The initialization is specific to the factory, so it belongs in the factory module
- **Lazy initialization**: Only imports when actually using the factory, not just importing the settings module
- **Clear documentation**: The pattern is documented in the helper function for future maintainers

## Acceptance Criteria

1. `create_task_service()` works when called from a module that only imports `tasky_settings` (no explicit `tasky_storage` import)
2. Backends are registered exactly once, even with multiple calls to `create_task_service()`
3. The initialization pattern is documented clearly for future backend authors
4. Test verifies isolated import scenario: import only from `tasky_settings` and verify factory works
5. No breaking changes to existing code

## Non-Goals

- Changing the backend self-registration pattern (keep import-time registration)
- Adding plugin system for dynamic backend discovery
- Removing the global registry singleton
- Making backends register themselves without import side effects

## Dependencies

This change has no dependencies. It can be implemented immediately.

## Risks and Mitigations

**Risk**: Import-time initialization could cause circular import issues
**Mitigation**: The import is in a function, called after all module definitions are loaded. Tested with existing circular import patterns in the codebase.

**Risk**: Future backends might not follow the self-registration pattern correctly
**Mitigation**: Documentation in `_ensure_backends_registered()` explains the pattern. Future SQLite backend will serve as second reference implementation.

**Risk**: Tests importing `tasky_storage` directly might not catch the isolation issue
**Mitigation**: Add dedicated test that imports only from `tasky_settings` to verify factory works standalone.

## Alternatives Considered

1. **Option A - Import in `__init__.py`**:
   - Add `import tasky_storage  # noqa: F401` to `tasky_settings/__init__.py`
   - **Rejected**: Forces import even when settings module is used for other purposes (config loading, etc.)

2. **Option B - Separate initialization function**:
   - Create `initialize_backends()` in `tasky_settings/__init__.py`
   - Require hosts to call it before using factory
   - **Rejected**: Moves the burden to callers, doesn't fix the "just works" problem

3. **Option D - Make registry import-aware**:
   - Modify `BackendRegistry.get()` to auto-import backends on demand
   - **Rejected**: Too magical, harder to debug, violates single responsibility

4. **Option E - Explicit backend imports in factory**:
   - Import specific backend classes in `create_task_service()` based on config
   - **Rejected**: Couples factory to specific backends, prevents plugin pattern

## Implementation Notes

- Keep `_backends_initialized` as module-level global to ensure single initialization
- Use `global` keyword clearly in `_ensure_backends_registered()`
- Add `# noqa: F401` to unused import (it's imported for side effects)
- Document the registration pattern in both the helper function and backend `__init__.py` files
- Consider adding a comment in `tasky_storage/__init__.py` referencing this pattern

## Related Changes

- Foundation for Phase 2 SQLite backend (same registration pattern)
- Enables future MCP server implementations
- Improves testability of service factory in isolation

## Migration Path

No migration needed - this is purely a fix for broken functionality. All existing code continues to work as-is, and new code gets the benefit of the fix automatically.
