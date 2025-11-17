# Spec Delta: test-utilities

## ADDED Requirements

### Requirement: Shared Test Repository Implementation

The tasky-tasks package SHALL provide a shared in-memory task repository implementation in `tests/conftest.py` to eliminate duplication of test infrastructure across multiple test files.

#### Repository Implementation

The `conftest.py` module SHALL provide `InMemoryTaskRepository` class with the following capabilities:

**Initialization modes**:
- `InMemoryTaskRepository()`: Create empty repository for mutable testing
- `InMemoryTaskRepository.from_tasks(tasks)`: Create pre-populated repository for filtering tests

**Protocol methods** (implementing TaskRepository):
- `initialize()`: Reset to empty state
- `save_task(task)`: Persist task to in-memory storage
- `get_task(task_id)`: Retrieve by ID or None
- `get_all_tasks()`: Return all tasks
- `get_tasks_by_status(status)`: Filter by status
- `find_tasks(filter)`: Apply TaskFilter criteria
- `delete_task(task_id)`: Remove task, return success boolean
- `task_exists(task_id)`: Check membership

**Design principles**:
- Mutable state (supports save/delete operations)
- Pre-populatable (via from_tasks class method)
- Resettable (via initialize for test cleanup)
- Comprehensive docstrings and type hints

#### Scenario: pytest discovers shared repository

```gherkin
Given InMemoryTaskRepository is defined in conftest.py
When a test file in tasky-tasks/tests imports no repository class
And the test creates an instance: repo = InMemoryTaskRepository()
Then pytest automatically discovers the class from conftest.py
And the repository is available for use
And no explicit import statement is required
```

#### Scenario: mutable repository for service tests

```gherkin
Given a test needs to verify service state changes
When the test creates an empty InMemoryTaskRepository()
And the test creates TaskService(repository)
And the test calls service.create_task(...)
Then the task is saved to repository
And repository.task_exists(task_id) returns True
And repository.get_task(task_id) returns the task
```

#### Scenario: pre-populated repository for filtering tests

```gherkin
Given a test needs to verify filtering logic
And the test has 3 pre-created TaskModel instances
When the test creates InMemoryTaskRepository.from_tasks([task1, task2, task3])
And the test creates TaskService(repository)
And the test calls service.find_tasks(filter)
Then the service queries the pre-populated repository
And filtering works against the 3 tasks
And no save operations are needed
```

#### Scenario: repository reset between tests

```gherkin
Given a repository contains tasks from a previous test
When the test calls repository.initialize()
Then repository.get_all_tasks() returns empty list
And repository.task_exists(any_id) returns False
And the repository is ready for new test
```

---

## MODIFIED Requirements

None. This change adds shared test infrastructure without modifying existing requirements.

---

## REMOVED Requirements

None. All existing requirements are preserved.
