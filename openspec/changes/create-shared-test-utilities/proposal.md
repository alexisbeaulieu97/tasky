# Change: Create Shared Test Utilities

## Why

The test suite has significant duplication of test infrastructure components across multiple packages:

**Duplicate test repository implementations**:
- `InMemoryTaskRepository` defined in `test_service.py` (57 lines)
- `MockTaskRepository` defined in `test_service_filtering.py` (38 lines)
- Both implement identical TaskRepository protocol with minor variations
- Used across multiple test files for service testing

**Duplicate task creation patterns**:
- `TaskModel(name="Test Task", details="Test details")` appears 43 times across 5 test files
- No shared factory functions for creating test tasks
- Each test file reimplements task creation with slightly different patterns

**Fragmented test infrastructure**:
- No centralized location for test utilities
- Each package defines its own test helpers
- New contributors don't know where to find or add shared test utilities
- Test code is harder to maintain than production code due to duplication

**Scalability issues**:
- As project grows, more tests will need fake repositories
- Future packages (tasky-api, tasky-mcp) will duplicate these utilities again
- No established pattern for "where do shared test utilities live?"

This violates the DRY principle and creates maintenance burden. The project needs a centralized location for shared test utilities that all packages can import.

## What Changes

Create a new package `tasky-testing` containing shared test utilities:

**New package structure**:
```
packages/tasky-testing/
  pyproject.toml              # Test utilities package
  src/tasky_testing/
    __init__.py               # Public API exports
    repositories.py           # Fake repository implementations
    factories.py              # Test data factories
```

**Shared components**:
1. **InMemoryTaskRepository**: Production-quality fake repository for testing
   - Implements full TaskRepository protocol
   - In-memory storage (no filesystem/database)
   - Used for isolated unit tests

2. **Task factories**: Helper functions for creating test tasks
   - `create_test_task(name, details, ...)` → TaskModel
   - `create_completed_task()` → TaskModel in completed state
   - `create_cancelled_task()` → TaskModel in cancelled state
   - Sensible defaults reduce boilerplate

3. **Assertion helpers**: Common test assertions
   - `assert_task_matches(actual, expected)` → compare task fields
   - `assert_tasks_equal(tasks1, tasks2)` → compare task lists

**Refactor existing tests**:
- Update `test_service.py` to use `tasky_testing.InMemoryTaskRepository`
- Update `test_service_filtering.py` to use shared repository
- Update tests using `TaskModel(name="Test Task", ...)` to use factories
- Remove duplicate repository implementations

**Benefits**:
- **Single source of truth**: One canonical fake repository implementation
- **Reduced boilerplate**: Tests use factories instead of manual task creation
- **Maintainability**: Changes to test infrastructure only require one update
- **Discoverability**: New contributors know where to find/add test utilities
- **Consistency**: All tests use same test data patterns
- **Future-proof**: New packages can import `tasky-testing` utilities

## Impact

- **Affected specs**: `test-utilities` (new spec defining shared test infrastructure)
- **Affected code**:
  - NEW: `packages/tasky-testing/` package
  - `packages/tasky-tasks/tests/test_service.py` - use shared repository
  - `packages/tasky-tasks/tests/test_service_filtering.py` - use shared repository
  - Multiple test files - use factories for task creation
- **Backward compatibility**: Zero breaking changes (test-only refactoring)
- **Testing**: All 577 tests must continue to pass with zero behavioral changes
- **Lines of code reduction**: ~80-100 lines (remove duplicate repositories and task creation boilerplate)
- **Package structure**: Adds new `tasky-testing` package (dev dependency for all packages)
