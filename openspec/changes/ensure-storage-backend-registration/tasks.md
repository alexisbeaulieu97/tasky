# Implementation Tasks: Ensure Storage Backend Registration

This document outlines the implementation tasks for fixing the hidden backend registration dependency. This is a Phase 1.5 fix designed to be completed quickly (~0.5 hours) before Phase 2 SQLite work begins.

## Task Checklist

### Phase 1: Core Implementation (15 minutes)

- [ ] **Task 1.1**: Add backend initialization helper in factory module
  - Update `packages/tasky-settings/src/tasky_settings/factory.py`
  - Add module-level `_backends_initialized = False` flag
  - Implement `_ensure_backends_registered()` function with:
    - Global flag check and update
    - Import of `tasky_storage` with `# noqa: F401`
    - Comprehensive docstring explaining the pattern
  - **Validation**: Code compiles and type-checks

- [ ] **Task 1.2**: Call initialization in `create_task_service()`
  - Update `create_task_service()` function in same file
  - Add `_ensure_backends_registered()` call at the start
  - Add comment explaining why this is needed
  - **Validation**: Existing tests still pass

### Phase 2: Documentation (10 minutes)

- [ ] **Task 2.1**: Document the registration pattern in storage module
  - Update `packages/tasky-storage/src/tasky_storage/__init__.py`
  - Add comment block explaining:
    - Backend self-registration pattern
    - How `tasky_settings` ensures backends are loaded
    - Template for future backends to follow
  - **Validation**: Comments are clear and accurate

- [ ] **Task 2.2**: Update factory docstring
  - Enhance `create_task_service()` docstring
  - Remove mention of `KeyError: If configured backend is not registered`
  - Note that backends are auto-initialized on first use
  - **Validation**: Docstring accurately reflects new behavior

### Phase 3: Testing (15 minutes)

- [ ] **Task 3.1**: Add isolated import test
  - Create `packages/tasky-settings/tests/test_factory_isolation.py`
  - Test scenario: Import only from `tasky_settings`, verify factory works
  - Use subprocess or import isolation to ensure `tasky_storage` isn't pre-imported
  - Verify `registry.list_backends()` shows `["json"]` after factory call
  - **Validation**: Test passes and proves isolation works

- [ ] **Task 3.2**: Add initialization idempotency test
  - Add test in same file
  - Call `create_task_service()` multiple times
  - Verify backend is only registered once (check logs or registry state)
  - Ensure no errors on repeated calls
  - **Validation**: Test passes and proves single initialization

- [ ] **Task 3.3**: Verify existing tests still pass
  - Run `uv run pytest packages/tasky-settings/tests/`
  - Run `uv run pytest packages/tasky-cli/tests/`
  - Ensure no regressions from the change
  - **Validation**: All existing tests pass

### Phase 4: Final Validation (5 minutes)

- [ ] **Task 4.1**: Run full test suite
  - Execute `uv run pytest` across all packages
  - Verify no unexpected failures
  - Check test coverage for new code
  - **Validation**: All tests pass, coverage ≥80%

- [ ] **Task 4.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - **Validation**: Code passes all quality checks

- [ ] **Task 4.3**: Manual smoke test
  - Create simple Python script that imports only `tasky_settings`
  - Call `create_task_service()` from a test project
  - Verify it works without explicit `tasky_storage` import
  - **Validation**: Factory works in isolation

## Implementation Order

Tasks must be completed sequentially:
1. Core implementation (1.1 → 1.2)
2. Documentation (2.1 → 2.2) - can overlap with testing
3. Testing (3.1 → 3.2 → 3.3)
4. Final validation (4.1 → 4.2 → 4.3)

## Notes

- **Keep it Simple**: This is a minimal fix, not a refactor. Don't change the registration pattern.
- **Single Responsibility**: Only fix the factory initialization, don't modify registry or backends.
- **Documentation Focus**: The pattern should be clear enough for future backend authors to follow.
- **Test Isolation**: The isolation test is critical - it proves the fix works without relying on import order luck.

## Estimated Duration

- Phase 1: 15 minutes
- Phase 2: 10 minutes
- Phase 3: 15 minutes
- Phase 4: 5 minutes

**Total**: ~45 minutes (0.75 hours, rounded to 0.5 hours in proposal)

## Success Criteria

The change is complete when:
1. ✅ Any host can import `create_task_service` and use it without importing `tasky_storage`
2. ✅ Tests prove isolation works
3. ✅ Pattern is documented for future backends
4. ✅ No existing functionality is broken
5. ✅ Code passes all quality checks
