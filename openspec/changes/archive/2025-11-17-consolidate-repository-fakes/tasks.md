# Tasks: Consolidate Test Repository Fakes

## 1. Create Shared Repository in conftest.py

- [x] 1.1 Create `packages/tasky-tasks/tests/conftest.py`
- [x] 1.2 Add module docstring: "Shared test fixtures for tasky-tasks package"
- [x] 1.3 Add imports: UUID, TaskFilter, TaskModel, TaskStatus
- [x] 1.4 Implement `InMemoryTaskRepository` class with comprehensive docstring
- [x] 1.5 Implement `__init__(self)`: Initialize empty dict
- [x] 1.6 Implement `from_tasks(cls, tasks)`: Class method for pre-population
- [x] 1.7 Implement `initialize(self)`: Clear dict
- [x] 1.8 Implement `save_task`, `get_task`, `get_all_tasks` methods
- [x] 1.9 Implement `get_tasks_by_status`, `find_tasks`, `delete_task`, `task_exists` methods
- [x] 1.10 Add type hints and docstrings for all methods
- [x] 1.11 Run `uv run pytest packages/tasky-tasks/tests/ --collect-only` to verify pytest loads conftest.py

## 2. Migrate test_service.py

- [x] 2.1 Remove local `InMemoryTaskRepository` class definition (lines 15-56)
- [x] 2.2 Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
- [x] 2.3 Verify all test_service.py tests pass

## 3. Migrate test_service_filtering.py

- [x] 3.1 Remove local `MockTaskRepository` class definition (lines 18-55)
- [x] 3.2 Replace all `MockTaskRepository(tasks=[...])` with `InMemoryTaskRepository.from_tasks([...])`
- [x] 3.3 Run `uv run pytest packages/tasky-tasks/tests/test_service_filtering.py -v`
- [x] 3.4 Verify all test_service_filtering.py tests pass

## 4. Final Validation

- [x] 4.1 Run full tasky-tasks test suite: `uv run pytest packages/tasky-tasks/tests/ -v`
- [x] 4.2 Run `uv run ruff check packages/tasky-tasks/tests/`
- [x] 4.3 Run `uv run pyright packages/tasky-tasks/tests/`
- [x] 4.4 Verify git diff shows expected line reduction (~30 net lines removed)
- [x] 4.5 Run full test suite (all packages): `uv run pytest`
- [x] 4.6 Verify all 577 tests pass
