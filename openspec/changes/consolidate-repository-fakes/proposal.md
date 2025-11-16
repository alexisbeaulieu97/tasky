# Change: Consolidate Test Repository Fakes

## Why

The test suite has duplicate implementations of in-memory task repository fakes used for isolated unit testing:

**Evidence**:
- `InMemoryTaskRepository` in `test_service.py` (57 lines, lines 15-56)
- `MockTaskRepository` in `test_service_filtering.py` (38 lines, lines 18-55)
- Both implement the same TaskRepository protocol
- Total duplication: ~95 lines

**Problem**:
- Changes to TaskRepository protocol require updating 2 locations
- Implementations have minor differences (mutable vs immutable) despite serving same purpose
- No clear "canonical" implementation for new tests to use
- Violates DRY principle in test code

## What Changes

Move the in-memory repository implementation to a shared location accessible by all tasky-tasks tests:

**Approach**: Extract to `packages/tasky-tasks/tests/conftest.py`
- pytest automatically discovers fixtures in conftest.py
- Available to all tests in tasky-tasks package
- No new package needed (uses existing pytest convention)
- Zero import complexity (pytest handles discovery)

**Unified implementation**:
- Combine best aspects of both existing implementations
- Production-quality: full protocol implementation, comprehensive docstrings
- Flexible: supports both pre-populated (test_service_filtering use case) and empty initialization (test_service use case)

**Result**:
- Remove ~95 lines of duplicate code
- Single source of truth for test repository
- Future tests automatically have access to fake repository

## Impact

- **Affected specs**: test-utilities (new spec for shared test infrastructure)
- **Affected code**:
  - NEW: `packages/tasky-tasks/tests/conftest.py` (~65 lines)
  - MODIFIED: `packages/tasky-tasks/tests/test_service.py` (remove InMemoryTaskRepository, -57 lines)
  - MODIFIED: `packages/tasky-tasks/tests/test_service_filtering.py` (remove MockTaskRepository, refactor tests, -38 lines)
  - Net line reduction: ~30 lines
- **Backward compatibility**: Zero breaking changes (test-only refactoring)
- **Testing**: All 577 tests must pass without behavioral changes
- **Risk**: Low (conftest.py is standard pytest pattern)
