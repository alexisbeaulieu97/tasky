# Design: Create Shared Test Utilities

## Problem Analysis

### Current State

**Duplicate repository implementations**:

1. **InMemoryTaskRepository** (`test_service.py`, lines 15-56):
   - 57 lines implementing full TaskRepository protocol
   - In-memory dict storage
   - Used for testing TaskService methods

2. **MockTaskRepository** (`test_service_filtering.py`, lines 18-55):
   - 38 lines implementing TaskRepository protocol
   - Accepts pre-populated task list
   - Used for filtering tests

**Differences**:
- `InMemoryTaskRepository`: Mutable state, `initialize()` clears state
- `MockTaskRepository`: Immutable task list passed at construction
- Both implement same protocol, could be unified

**Task creation duplication**:
- 43 instances of `TaskModel(name="Test Task", details="Test details")` across 5 files
- No standard factory pattern
- Each test creates tasks manually with slightly different values

### Infrastructure Gap

**No dedicated test utilities package**:
- Test helpers scattered across individual test files
- No discoverable location for shared utilities
- As project scales, duplication will worsen

## Design Decision: Create tasky-testing Package

### Option 1: Keep test helpers in each package (REJECTED)
Continue with current approach of defining helpers per package.

**Pros**: No new package needed
**Cons**: Duplication; no shared infrastructure; scales poorly

### Option 2: Add test_utils.py to each package (REJECTED)
Create `tests/test_utils.py` in each package with shared helpers.

**Pros**: Helpers within package scope
**Cons**: Still duplicates fake repository across packages; no cross-package sharing

### Option 3: Create tasky-testing package (SELECTED)
Create dedicated package for test utilities usable by all packages.

**Pros**:
- Single source of truth for test infrastructure
- All packages can import shared utilities
- Clear location for test helpers (discoverability)
- Follows industry pattern (pytest, factory_boy, faker)
- Can grow to include more utilities (builders, matchers, etc.)

**Cons**: Adds new package (minimal cost, test-only dependency)

**Decision**: Option 3. Create `tasky-testing` as dedicated test utilities package.

## Package Design

### tasky-testing Package Structure

```
packages/tasky-testing/
  pyproject.toml
  README.md
  src/tasky_testing/
    __init__.py              # Public API
    repositories.py          # Fake repository implementations
    factories.py             # Test data factories
    matchers.py              # Custom assertion helpers (future)
  tests/
    test_repositories.py     # Test the test infrastructure!
```

**pyproject.toml**:
```toml
[project]
name = "tasky-testing"
version = "0.1.0"
description = "Shared test utilities for Tasky project"
requires-python = ">=3.13"
dependencies = [
    "tasky-tasks",  # Need TaskModel, TaskRepository protocol
]
```

**Package installation**:
- Add `tasky-testing` as dev dependency in root `pyproject.toml`
- All packages can import: `from tasky_testing import InMemoryTaskRepository`

---

### Module: repositories.py

**Responsibility**: Provide fake repository implementations for testing

**InMemoryTaskRepository Implementation**:
```python
\"\"\"Fake repository implementations for testing.

This module provides in-memory test doubles for repository protocols,
allowing tests to run without actual storage backends.
\"\"\"

from __future__ import annotations

from uuid import UUID

from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


class InMemoryTaskRepository:
    \"\"\"In-memory task repository for isolated testing.

    Implements the TaskRepository protocol without requiring actual storage.
    State is mutable and can be reset with initialize().

    Example:
        >>> repo = InMemoryTaskRepository()
        >>> service = TaskService(repo)
        >>> task = service.create_task("Test", "Details")
        >>> assert repo.task_exists(task.task_id)
    \"\"\"

    def __init__(self) -> None:
        \"\"\"Initialize empty repository.\"\"\"
        self.tasks: dict[UUID, TaskModel] = {}

    def initialize(self) -> None:
        \"\"\"Reset repository to empty state.\"\"\"
        self.tasks.clear()

    def save_task(self, task: TaskModel) -> None:
        \"\"\"Persist a task to in-memory storage.\"\"\"
        self.tasks[task.task_id] = task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        \"\"\"Retrieve task by ID, or None if not found.\"\"\"
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        \"\"\"Return all stored tasks.\"\"\"
        return list(self.tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        \"\"\"Return tasks filtered by status.\"\"\"
        return [task for task in self.tasks.values() if task.status == status]

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        \"\"\"Return tasks matching filter criteria.\"\"\"
        return [task for task in self.tasks.values() if task_filter.matches(task)]

    def delete_task(self, task_id: UUID) -> bool:
        \"\"\"Remove task from storage, returning True if existed.\"\"\"
        return self.tasks.pop(task_id, None) is not None

    def task_exists(self, task_id: UUID) -> bool:
        \"\"\"Check if task exists in storage.\"\"\"
        return task_id in self.tasks
```

**Design notes**:
- Unified implementation (combines best of both existing fakes)
- Production-quality: comprehensive docstrings, type hints
- Testable: repository itself has unit tests

---

### Module: factories.py

**Responsibility**: Provide factory functions for creating test data

**Factory functions**:
```python
\"\"\"Factory functions for creating test data.

Factories reduce boilerplate in tests by providing sensible defaults
for common test scenarios.
\"\"\"

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from tasky_tasks.models import TaskModel, TaskStatus


def create_test_task(
    name: str = "Test Task",
    details: str = "Test details",
    *,
    task_id: UUID | None = None,
    status: TaskStatus = TaskStatus.PENDING,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> TaskModel:
    \"\"\"Create a task for testing with sensible defaults.

    Args:
        name: Task name (default: "Test Task")
        details: Task details (default: "Test details")
        task_id: Task UUID (default: random UUID)
        status: Task status (default: PENDING)
        created_at: Creation timestamp (default: now in UTC)
        updated_at: Update timestamp (default: same as created_at)

    Returns:
        TaskModel configured for testing

    Example:
        >>> task = create_test_task()  # All defaults
        >>> task = create_test_task("Buy groceries", status=TaskStatus.COMPLETED)
    \"\"\"
    now = datetime.now(UTC)
    return TaskModel(
        task_id=task_id or uuid4(),
        name=name,
        details=details,
        status=status,
        created_at=created_at or now,
        updated_at=updated_at or created_at or now,
    )


def create_completed_task(
    name: str = "Completed Task",
    details: str = "Task is done",
) -> TaskModel:
    \"\"\"Create a task in COMPLETED state.

    Convenience factory for testing completed task scenarios.

    Args:
        name: Task name
        details: Task details

    Returns:
        TaskModel with status=COMPLETED
    \"\"\"
    task = create_test_task(name=name, details=details)
    task.complete()
    return task


def create_cancelled_task(
    name: str = "Cancelled Task",
    details: str = "Task was cancelled",
) -> TaskModel:
    \"\"\"Create a task in CANCELLED state.

    Convenience factory for testing cancelled task scenarios.

    Args:
        name: Task name
        details: Task details

    Returns:
        TaskModel with status=CANCELLED
    \"\"\"
    task = create_test_task(name=name, details=details)
    task.cancel()
    return task


def create_task_batch(count: int, *, name_prefix: str = "Task") -> list[TaskModel]:
    \"\"\"Create multiple tasks for testing.

    Args:
        count: Number of tasks to create
        name_prefix: Prefix for task names (numbered)

    Returns:
        List of TaskModel instances

    Example:
        >>> tasks = create_task_batch(5, name_prefix="Import")
        >>> # Creates: "Import 1", "Import 2", ..., "Import 5"
    \"\"\"
    return [
        create_test_task(name=f"{name_prefix} {i + 1}")
        for i in range(count)
    ]
```

**Design notes**:
- Sensible defaults reduce boilerplate
- Keyword-only args for clarity
- Convenience functions for common states
- Batch creation for list testing scenarios

---

### Module: matchers.py (Future Enhancement, Not in This Change)

**Potential utilities** (deferred):
```python
def assert_task_matches(actual: TaskModel, expected: TaskModel) -> None:
    \"\"\"Assert two tasks have matching fields.\"\"\"
    ...

def assert_tasks_equal(tasks1: list[TaskModel], tasks2: list[TaskModel]) -> None:
    \"\"\"Assert two task lists are equivalent.\"\"\"
    ...
```

**Decision**: Start with repositories and factories. Add matchers later if needed.

## Migration Strategy

### Phase 1: Create tasky-testing Package
1. Create package directory structure
2. Add `pyproject.toml` with dependencies
3. Create `__init__.py` with public API exports
4. Create `repositories.py` with `InMemoryTaskRepository`
5. Create `factories.py` with task creation functions
6. Add unit tests for the test infrastructure
7. Add to workspace dependencies

### Phase 2: Migrate Existing Tests
**test_service.py**:
1. Replace local `InMemoryTaskRepository` with import from `tasky_testing`
2. Remove duplicate definition (lines 15-56)
3. Update tests to use factories where appropriate
4. Run tests → verify behavioral equivalence

**test_service_filtering.py**:
1. Replace `MockTaskRepository` with `InMemoryTaskRepository` from `tasky_testing`
2. Refactor tests to populate repository state instead of passing task list
3. Update tests to use factories
4. Run tests → verify behavioral equivalence

**Other test files**:
1. Search for `TaskModel(name="Test Task"` patterns
2. Replace with `create_test_task()` factory calls
3. Verify tests pass

### Phase 3: Update Documentation
1. Add README.md to tasky-testing package
2. Document available utilities
3. Add examples for common patterns
4. Update contributor documentation

## Testing Strategy

### Test the Test Infrastructure
**packages/tasky-testing/tests/test_repositories.py**:
- Test `InMemoryTaskRepository` implements protocol correctly
- Test `initialize()` clears state
- Test all CRUD operations
- Test filtering and status queries

**packages/tasky-testing/tests/test_factories.py**:
- Test `create_test_task()` with defaults
- Test `create_test_task()` with custom values
- Test `create_completed_task()` has correct status
- Test `create_cancelled_task()` has correct status
- Test `create_task_batch()` creates correct count

### Behavioral Equivalence Tests
- All 577 existing tests must pass after migration
- Test output should be identical (factories produce same data)
- No changes to test logic required (drop-in replacement)

## Success Criteria

✅ `tasky-testing` package created with proper structure
✅ `InMemoryTaskRepository` implemented with comprehensive tests
✅ Task factories implemented with comprehensive tests
✅ Duplicate repository implementations removed from test_service.py and test_service_filtering.py
✅ Manual `TaskModel(...)` creation replaced with factories (where appropriate)
✅ All 577 tests pass with zero behavioral changes
✅ ~80-100 lines of duplicate code removed
✅ README.md documents available utilities
✅ Zero linting or type errors in new package
