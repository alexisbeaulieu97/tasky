# Tasks: Consolidate Test Repository Fakes

## Phase 1: Create Shared Repository in conftest.py

### Task 1.1: Create conftest.py with InMemoryTaskRepository
- Create `packages/tasky-tasks/tests/conftest.py`
- Add module docstring: "Shared test fixtures for tasky-tasks package"
- Add necessary imports (UUID, TaskFilter, TaskModel, TaskStatus)
- **Acceptance**: File exists with proper structure

### Task 1.2: Implement InMemoryTaskRepository class
- Add class with comprehensive docstring
- Implement `__init__(self)`: Initialize empty dict
- Implement `from_tasks(cls, tasks)`: Class method for pre-population
- Implement `initialize(self)`: Clear dict
- Implement all 7 TaskRepository protocol methods:
  - `save_task`
  - `get_task`
  - `get_all_tasks`
  - `get_tasks_by_status`
  - `find_tasks`
  - `delete_task`
  - `task_exists`
- Add type hints for all methods
- Add docstrings for all methods
- **Acceptance**: Full protocol implementation with ~65 lines

### Task 1.3: Verify pytest discovers the class
- Run `uv run pytest packages/tasky-tasks/tests/ --collect-only`
- Verify conftest.py is loaded
- Verify no import errors
- **Acceptance**: pytest successfully loads conftest.py

## Phase 2: Migrate test_service.py

### Task 2.1: Remove local InMemoryTaskRepository
- Open `packages/tasky-tasks/tests/test_service.py`
- Remove class definition (lines 15-56, 42 lines)
- Remove now-unnecessary docstring about avoiding circular dependencies
- **Acceptance**: Local InMemoryTaskRepository removed

### Task 2.2: Verify tests use conftest.py version
- Tests should automatically use conftest.py version (pytest discovers it)
- No explicit import needed
- Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
- **Acceptance**: All test_service.py tests pass

## Phase 3: Migrate test_service_filtering.py

### Task 3.1: Remove local MockTaskRepository
- Open `packages/tasky-tasks/tests/test_service_filtering.py`
- Remove class definition (lines 18-55, 38 lines)
- **Acceptance**: Local MockTaskRepository removed

### Task 3.2: Refactor tests to use from_tasks()
- Find all instances of `MockTaskRepository(tasks=[...])`
- Replace with `InMemoryTaskRepository.from_tasks([...])`
- Example locations:
  - Test setup in filtering test cases
  - Test fixtures that create repository with pre-populated tasks
- **Acceptance**: All MockTaskRepository uses replaced

### Task 3.3: Verify refactored tests pass
- Run `uv run pytest packages/tasky-tasks/tests/test_service_filtering.py -v`
- Verify all filtering tests pass
- Verify filtering logic works with new repository
- **Acceptance**: All test_service_filtering.py tests pass

## Phase 4: Final Validation

### Task 4.1: Run full tasky-tasks test suite
- Run `uv run pytest packages/tasky-tasks/tests/ -v`
- Verify all tests pass
- **Acceptance**: Complete tasky-tasks test suite passes

### Task 4.2: Verify code quality
- Run `uv run ruff check packages/tasky-tasks/tests/`
- Run `uv run pyright packages/tasky-tasks/tests/`
- **Acceptance**: Zero linting or type errors

### Task 4.3: Verify line count reduction
- Check git diff:
  - conftest.py: +65 lines (new file)
  - test_service.py: -57 lines (removed duplicate)
  - test_service_filtering.py: -38 lines (removed duplicate)
  - Net: -30 lines
- **Acceptance**: Expected line reduction achieved

### Task 4.4: Run full test suite (all packages)
- Run `uv run pytest`
- Verify all 577 tests pass
- **Acceptance**: No regressions in other packages
