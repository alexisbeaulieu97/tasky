# Design: Consolidate Test Repository Fakes

## Problem Analysis

### Current State

**InMemoryTaskRepository** (`test_service.py`, lines 15-56, 57 lines):
```python
class InMemoryTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[UUID, TaskModel] = {}

    def initialize(self) -> None:
        self.tasks.clear()

    # ... 7 protocol methods ...
```

**MockTaskRepository** (`test_service_filtering.py`, lines 18-55, 38 lines):
```python
class MockTaskRepository:
    def __init__(self, tasks: list[TaskModel] | None = None) -> None:
        self.tasks = tasks or []

    # ... 7 protocol methods (read-only, uses list) ...
```

**Differences**:
1. **Storage**: InMemory uses dict (mutable), Mock uses list (read-only)
2. **Initialization**: InMemory has `initialize()` to reset, Mock doesn't
3. **Pre-population**: Mock accepts tasks at construction, InMemory doesn't
4. **Mutability**: InMemory supports save/delete, Mock is read-only

### Use Cases

**test_service.py use cases**:
- Create service, call methods, verify state changes
- Needs mutable repository (save_task, delete_task work)
- Needs reset capability (`initialize()` between tests)

**test_service_filtering.py use cases**:
- Create service with pre-populated tasks
- Test find_tasks() with various filters
- Needs read-only repository (tasks list doesn't change)

## Design Decision

### Option 1: Keep both implementations (REJECTED)

**Benefit**: 0/5 (no improvement)
**Cost**: 0/5 (no change)
**Score**: 0/5

Keep status quo. Violates DRY.

### Option 2: Create tasky-testing package (REJECTED)

**Benefit**: 3/5 (removes duplication, 2 uses)
**Cost**: 4/5 (new package, pyproject.toml, infrastructure)
**Score**: -1/5 (premature abstraction)

Over-engineering for 2 duplicate implementations.

### Option 3: Move to conftest.py (SELECTED)

**Benefit**: 3/5 (removes duplication, standard pattern)
**Cost**: 1/5 (move to existing file, minimal refactoring)
**Score**: 2/5 (marginal yes)

**Pros**:
- Standard pytest pattern (conftest.py for shared fixtures)
- Automatically discovered by all tests in package
- Zero new infrastructure
- Combines best of both implementations

**Cons**:
- Only available within tasky-tasks package (but that's where it's needed)

## Unified Implementation Design

### InMemoryTaskRepository (Unified)

**Location**: `packages/tasky-tasks/tests/conftest.py`

**Design goals**:
1. Support both use cases (mutable + pre-populated)
2. Production-quality (comprehensive docstrings, type hints)
3. Full protocol implementation

**Implementation**:
```python
"""Shared test fixtures for tasky-tasks package."""

from uuid import UUID

from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus


class InMemoryTaskRepository:
    """In-memory task repository for isolated unit testing.

    Implements the TaskRepository protocol without requiring actual storage.
    Supports both mutable operations (save/delete) and pre-population with test data.

    Attributes:
        tasks: Internal dict mapping UUID to TaskModel

    Example (mutable use):
        >>> repo = InMemoryTaskRepository()
        >>> service = TaskService(repo)
        >>> task = service.create_task("Test", "Details")
        >>> assert repo.task_exists(task.task_id)

    Example (pre-populated use):
        >>> task1 = TaskModel(name="Task 1", details="...")
        >>> task2 = TaskModel(name="Task 2", details="...")
        >>> repo = InMemoryTaskRepository.from_tasks([task1, task2])
        >>> assert len(repo.get_all_tasks()) == 2
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self.tasks: dict[UUID, TaskModel] = {}

    @classmethod
    def from_tasks(cls, tasks: list[TaskModel]) -> "InMemoryTaskRepository":
        """Create repository pre-populated with tasks.

        Args:
            tasks: List of tasks to include in repository

        Returns:
            Repository instance with tasks pre-loaded
        """
        repo = cls()
        for task in tasks:
            repo.tasks[task.task_id] = task
        return repo

    def initialize(self) -> None:
        """Reset repository to empty state.

        Useful for test cleanup between test cases.
        """
        self.tasks.clear()

    def save_task(self, task: TaskModel) -> None:
        """Persist a task to in-memory storage."""
        self.tasks[task.task_id] = task

    def get_task(self, task_id: UUID) -> TaskModel | None:
        """Retrieve task by ID, or None if not found."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[TaskModel]:
        """Return all stored tasks."""
        return list(self.tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> list[TaskModel]:
        """Return tasks filtered by status."""
        return [task for task in self.tasks.values() if task.status == status]

    def find_tasks(self, task_filter: TaskFilter) -> list[TaskModel]:
        """Return tasks matching filter criteria."""
        return [task for task in self.tasks.values() if task_filter.matches(task)]

    def delete_task(self, task_id: UUID) -> bool:
        """Remove task from storage, returning True if existed."""
        return self.tasks.pop(task_id, None) is not None

    def task_exists(self, task_id: UUID) -> bool:
        """Check if task exists in storage."""
        return task_id in self.tasks
```

**Key features**:
- **Mutable**: Supports all CRUD operations
- **Pre-populatable**: `from_tasks()` class method for filtering tests
- **Resettable**: `initialize()` for test cleanup
- **Comprehensive**: Full protocol, proper docstrings

## Migration Strategy

### Phase 1: Add Unified Implementation to conftest.py
1. Create `packages/tasky-tasks/tests/conftest.py`
2. Add `InMemoryTaskRepository` class
3. Run tests → verify pytest discovers it

### Phase 2: Migrate test_service.py
1. Remove local `InMemoryTaskRepository` definition (lines 15-56)
2. Tests automatically use conftest.py version (pytest discovers it)
3. Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
4. Verify all tests pass

### Phase 3: Migrate test_service_filtering.py
1. Remove local `MockTaskRepository` definition (lines 18-55)
2. Refactor tests to use `InMemoryTaskRepository.from_tasks()`
3. Example refactor:
   ```python
   # Before:
   repository = MockTaskRepository(tasks=[task1, task2, task3])
   service = TaskService(repository)

   # After:
   repository = InMemoryTaskRepository.from_tasks([task1, task2, task3])
   service = TaskService(repository)
   ```
4. Run `uv run pytest packages/tasky-tasks/tests/test_service_filtering.py -v`
5. Verify all tests pass

### Phase 4: Final Validation
1. Run full tasky-tasks test suite: `uv run pytest packages/tasky-tasks/tests/ -v`
2. Verify all tests pass
3. Run linting and type checking

## Testing Strategy

- All existing tests must pass without modification to test logic
- pytest automatically discovers InMemoryTaskRepository from conftest.py
- No changes to test assertions or expected behavior

## Success Criteria

✅ `InMemoryTaskRepository` exists in conftest.py
✅ Duplicate definitions removed from test_service.py and test_service_filtering.py
✅ All tasky-tasks tests pass (no behavioral changes)
✅ ~95 lines of duplicate code removed
✅ Net ~30 line reduction
✅ Future tests automatically have access to fake repository
