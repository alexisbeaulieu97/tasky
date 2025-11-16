# Tasks: Consolidate Test Repository Fakes

## 1. Create Shared Repository in conftest.py

- [ ] 1.1 Create `packages/tasky-tasks/tests/conftest.py`
- [ ] 1.2 Add module docstring: "Shared test fixtures for tasky-tasks package"
- [ ] 1.3 Add imports: UUID, TaskFilter, TaskModel, TaskStatus
- [ ] 1.4 Implement `InMemoryTaskRepository` class with comprehensive docstring
- [ ] 1.5 Implement `__init__(self)`: Initialize empty dict
- [ ] 1.6 Implement `from_tasks(cls, tasks)`: Class method for pre-population
- [ ] 1.7 Implement `initialize(self)`: Clear dict
- [ ] 1.8 Implement `save_task`, `get_task`, `get_all_tasks` methods
- [ ] 1.9 Implement `get_tasks_by_status`, `find_tasks`, `delete_task`, `task_exists` methods
- [ ] 1.10 Add type hints and docstrings for all methods
- [ ] 1.11 Run `uv run pytest packages/tasky-tasks/tests/ --collect-only` to verify pytest loads conftest.py

## 2. Migrate test_service.py

- [ ] 2.1 Remove local `InMemoryTaskRepository` class definition (lines 15-56)
- [ ] 2.2 Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
- [ ] 2.3 Verify all test_service.py tests pass

## 3. Migrate test_service_filtering.py

- [ ] 3.1 Remove local `MockTaskRepository` class definition (lines 18-55)
- [ ] 3.2 Replace all `MockTaskRepository(tasks=[...])` with `InMemoryTaskRepository.from_tasks([...])`
- [ ] 3.3 Run `uv run pytest packages/tasky-tasks/tests/test_service_filtering.py -v`
- [ ] 3.4 Verify all test_service_filtering.py tests pass

## 4. Final Validation

- [ ] 4.1 Run full tasky-tasks test suite: `uv run pytest packages/tasky-tasks/tests/ -v`
- [ ] 4.2 Run `uv run ruff check packages/tasky-tasks/tests/`
- [ ] 4.3 Run `uv run pyright packages/tasky-tasks/tests/`
- [ ] 4.4 Verify git diff shows expected line reduction (~30 net lines removed)
- [ ] 4.5 Run full test suite (all packages): `uv run pytest`
- [ ] 4.6 Verify all 577 tests pass
