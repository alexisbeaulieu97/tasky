# Spec Delta: test-utilities

## ADDED Requirements

### Requirement: Shared Test Utilities Package

The project SHALL provide a dedicated `tasky-testing` package containing shared test utilities, fake implementations, and test data factories to eliminate code duplication across test suites and establish consistent testing patterns.

#### Package Structure

The tasky-testing package SHALL be organized as follows:

```
packages/tasky-testing/
  pyproject.toml              # Package configuration
  README.md                   # Documentation for test utilities
  src/tasky_testing/
    __init__.py               # Public API exports
    repositories.py           # Fake repository implementations
    factories.py              # Test data factories
  tests/
    test_repositories.py      # Tests for fake repositories
    test_factories.py         # Tests for factory functions
```

**Dependencies:**
- The package SHALL depend on `tasky-tasks` for TaskModel and protocol definitions
- The package SHALL be installed as a dev dependency in all packages that use it
- The package SHALL NOT depend on storage backends (uses in-memory implementations)

**Public API:**
- All public utilities SHALL be exported from `__init__.py`
- Users SHALL import utilities via: `from tasky_testing import InMemoryTaskRepository, create_test_task`
- Internal implementation details SHALL NOT be exported

#### Scenario: Package is importable by all test suites

```gherkin
Given the tasky-testing package is installed as a dev dependency
When a test file imports "from tasky_testing import InMemoryTaskRepository"
Then the import succeeds without error
And the repository is ready to use in tests
And no storage backend dependencies are required
```

---

### Requirement: In-Memory Task Repository

The tasky-testing package SHALL provide an `InMemoryTaskRepository` class implementing the TaskRepository protocol using in-memory storage for isolated, fast unit tests.

#### Repository Specification

The `InMemoryTaskRepository` SHALL:

1. Implement the full TaskRepository protocol from tasky-tasks
2. Store tasks in memory using a dict mapping UUID → TaskModel
3. Provide `initialize()` method to reset state between tests
4. Support all repository operations:
   - `save_task(task: TaskModel) -> None`
   - `get_task(task_id: UUID) -> TaskModel | None`
   - `get_all_tasks() -> list[TaskModel]`
   - `get_tasks_by_status(status: TaskStatus) -> list[TaskModel]`
   - `find_tasks(filter: TaskFilter) -> list[TaskModel]`
   - `delete_task(task_id: UUID) -> bool`
   - `task_exists(task_id: UUID) -> bool`

**Behavioral Contract:**
- State is mutable (tasks can be saved, retrieved, deleted)
- `initialize()` clears all stored tasks
- Operations are synchronous (no I/O)
- No persistence (data lost when object is garbage collected)
- Thread-safe for single-threaded tests (no concurrency guarantees)

#### Scenario: Repository provides isolated test environment

```gherkin
Given a test creates an InMemoryTaskRepository
When the test saves a task to the repository
And the test retrieves the task by ID
Then the task is returned successfully
And the task data matches what was saved
And changes are isolated to this test (no cross-test contamination)
```

#### Scenario: Initialize resets repository state

```gherkin
Given a repository contains 5 tasks
When initialize() is called
Then get_all_tasks() returns an empty list
And task_exists() returns False for all previous task IDs
And the repository is ready for new tests
```

#### Scenario: Repository supports filtering

```gherkin
Given a repository contains 3 pending tasks and 2 completed tasks
When get_tasks_by_status(TaskStatus.COMPLETED) is called
Then exactly 2 tasks are returned
And all returned tasks have status=COMPLETED
```

---

### Requirement: Test Data Factories

The tasky-testing package SHALL provide factory functions for creating TaskModel instances with sensible defaults to reduce boilerplate in tests.

#### Factory Functions

The factories.py module SHALL provide:

- `create_test_task(name, details, *, task_id, status, created_at, updated_at) -> TaskModel`
  - Create task with sensible defaults
  - All parameters optional except name and details
  - Default status: PENDING
  - Default timestamps: now in UTC

- `create_completed_task(name, details) -> TaskModel`
  - Create task in COMPLETED state
  - Calls `task.complete()` to ensure proper state transition

- `create_cancelled_task(name, details) -> TaskModel`
  - Create task in CANCELLED state
  - Calls `task.cancel()` to ensure proper state transition

- `create_task_batch(count, *, name_prefix) -> list[TaskModel]`
  - Create multiple tasks with numbered names
  - Example: `create_task_batch(3, name_prefix="Task")` → ["Task 1", "Task 2", "Task 3"]

**Design Principles:**
- Sensible defaults reduce boilerplate
- Keyword-only arguments for clarity
- Factories produce valid TaskModel instances
- State transitions use proper domain methods (complete(), cancel())

#### Scenario: Default task creation requires minimal arguments

```gherkin
Given a test needs a simple task for testing
When the test calls create_test_task()
Then a TaskModel is returned with:
  - name="Test Task"
  - details="Test details"
  - status=PENDING
  - created_at and updated_at set to current UTC time
  - random UUID assigned
```

#### Scenario: Factory allows custom values

```gherkin
Given a test needs a task with specific values
When the test calls create_test_task(name="Buy groceries", status=TaskStatus.COMPLETED)
Then a TaskModel is returned with:
  - name="Buy groceries"
  - status=COMPLETED
  - All other fields use sensible defaults
```

#### Scenario: Convenience factories create proper state

```gherkin
Given a test needs a completed task
When the test calls create_completed_task()
Then a TaskModel is returned
And task.status == TaskStatus.COMPLETED
And the task was transitioned using task.complete() method
And updated_at reflects the state transition
```

---

### Requirement: Test Infrastructure Documentation

The tasky-testing package SHALL provide comprehensive documentation to help developers discover and use shared test utilities.

#### Documentation Requirements

**README.md SHALL include:**
- Package purpose and benefits
- Installation instructions (dev dependency)
- Available utilities and their use cases
- Code examples for common patterns
- Guidelines for adding new test utilities

**Module docstrings SHALL include:**
- Purpose of each module
- Overview of available functions/classes
- Usage examples

**Function/class docstrings SHALL include:**
- Description of behavior
- Parameter documentation
- Return value documentation
- Usage examples where helpful

#### Scenario: New contributor finds test utilities

```gherkin
Given a new contributor needs to write tests for a new feature
When the contributor reads the tasky-testing README
Then they learn that shared test utilities exist
And they see examples of how to use InMemoryTaskRepository
And they see examples of how to use task factories
And they understand when to use each utility
```

---

## MODIFIED Requirements

None. This change adds new test infrastructure without modifying existing requirements.

---

## REMOVED Requirements

None. All existing requirements are preserved.
