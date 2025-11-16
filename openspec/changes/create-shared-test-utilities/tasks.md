# Tasks: Create Shared Test Utilities

## Phase 1: Create Package Structure

### Task 1.1: Create tasky-testing package directory
- Create `packages/tasky-testing/` directory
- Create `packages/tasky-testing/src/tasky_testing/` directory
- Create `packages/tasky-testing/tests/` directory
- **Acceptance**: Directory structure exists

### Task 1.2: Create package configuration
- Create `packages/tasky-testing/pyproject.toml` with:
  - name="tasky-testing"
  - version="0.1.0"
  - description="Shared test utilities for Tasky project"
  - requires-python=">=3.13"
  - dependencies=["tasky-tasks"]
- Add LICENSE and README.md placeholders
- **Acceptance**: Package is properly configured

### Task 1.3: Add to workspace dependencies
- Update root `pyproject.toml` to include tasky-testing as dev dependency
- Update workspace members to include `packages/tasky-testing`
- Run `uv sync` to install package
- **Acceptance**: Package is installed and importable

## Phase 2: Implement Repository Utilities

### Task 2.1: Create repositories.py module
- Create `packages/tasky-testing/src/tasky_testing/repositories.py`
- Add module docstring explaining purpose
- Add necessary imports:
  - `from uuid import UUID`
  - `from tasky_tasks.models import TaskFilter, TaskModel, TaskStatus`
- **Acceptance**: Module exists with proper structure

### Task 2.2: Implement InMemoryTaskRepository
- Implement `InMemoryTaskRepository` class
- Add `__init__()` method creating empty dict
- Implement all TaskRepository protocol methods:
  - `initialize()` → clear dict
  - `save_task(task)` → store in dict
  - `get_task(task_id)` → retrieve from dict
  - `get_all_tasks()` → return all values
  - `get_tasks_by_status(status)` → filter by status
  - `find_tasks(filter)` → filter by criteria
  - `delete_task(task_id)` → remove from dict
  - `task_exists(task_id)` → check membership
- Add comprehensive docstring with usage example
- Add type hints for all methods
- **Acceptance**: Repository implements full protocol with proper documentation

### Task 2.3: Create repository tests
- Create `packages/tasky-testing/tests/test_repositories.py`
- Test `initialize()` clears state
- Test `save_task()` and `get_task()` roundtrip
- Test `get_all_tasks()` returns all tasks
- Test `get_tasks_by_status()` filters correctly
- Test `find_tasks()` applies filter
- Test `delete_task()` removes task
- Test `task_exists()` checks membership
- Run `uv run pytest packages/tasky-testing/tests/test_repositories.py -v`
- **Acceptance**: Repository is thoroughly tested; all tests pass

## Phase 3: Implement Factory Utilities

### Task 3.1: Create factories.py module
- Create `packages/tasky-testing/src/tasky_testing/factories.py`
- Add module docstring explaining purpose
- Add necessary imports:
  - `from datetime import UTC, datetime`
  - `from uuid import UUID, uuid4`
  - `from tasky_tasks.models import TaskModel, TaskStatus`
- **Acceptance**: Module exists with proper structure

### Task 3.2: Implement create_test_task factory
- Implement `create_test_task()` function
- Parameters:
  - `name: str = "Test Task"`
  - `details: str = "Test details"`
  - `task_id: UUID | None = None` (keyword-only)
  - `status: TaskStatus = TaskStatus.PENDING` (keyword-only)
  - `created_at: datetime | None = None` (keyword-only)
  - `updated_at: datetime | None = None` (keyword-only)
- Default behavior:
  - Generate random UUID if not provided
  - Use current UTC time for timestamps if not provided
  - updated_at defaults to created_at if not provided
- Add comprehensive docstring with examples
- **Acceptance**: Factory creates tasks with sensible defaults

### Task 3.3: Implement convenience factories
- Implement `create_completed_task(name, details)`:
  - Create task using `create_test_task()`
  - Call `task.complete()` to transition state
  - Return completed task
- Implement `create_cancelled_task(name, details)`:
  - Create task using `create_test_task()`
  - Call `task.cancel()` to transition state
  - Return cancelled task
- Implement `create_task_batch(count, *, name_prefix)`:
  - Create list of `count` tasks
  - Name each task as `{name_prefix} {i+1}`
  - Return list of tasks
- Add comprehensive docstrings
- **Acceptance**: Convenience factories work correctly

### Task 3.4: Create factory tests
- Create `packages/tasky-testing/tests/test_factories.py`
- Test `create_test_task()` with defaults
- Test `create_test_task()` with custom values
- Test `create_test_task()` generates unique UUIDs
- Test `create_test_task()` uses UTC timestamps
- Test `create_completed_task()` has correct status
- Test `create_cancelled_task()` has correct status
- Test `create_task_batch()` creates correct count
- Test `create_task_batch()` numbers tasks correctly
- Run `uv run pytest packages/tasky-testing/tests/test_factories.py -v`
- **Acceptance**: Factories are thoroughly tested; all tests pass

## Phase 4: Public API and Documentation

### Task 4.1: Create public API exports
- Create `packages/tasky-testing/src/tasky_testing/__init__.py`
- Export `InMemoryTaskRepository` from repositories module
- Export all factory functions from factories module
- Add module docstring explaining package purpose
- Define `__all__` with exported names
- **Acceptance**: All utilities are importable from top-level package

### Task 4.2: Create package README
- Create `packages/tasky-testing/README.md`
- Document package purpose and benefits
- Document installation as dev dependency
- Provide examples for InMemoryTaskRepository usage
- Provide examples for factory function usage
- Document when to use each utility
- Include guidelines for adding new utilities
- **Acceptance**: Comprehensive README exists

### Task 4.3: Verify package can be imported
- Run `uv run python -c "from tasky_testing import InMemoryTaskRepository, create_test_task"`
- Verify no import errors
- Verify all exported utilities are accessible
- **Acceptance**: Package public API works correctly

## Phase 5: Migrate Existing Tests

### Task 5.1: Update test_service.py
- Open `packages/tasky-tasks/tests/test_service.py`
- Add import: `from tasky_testing import InMemoryTaskRepository`
- Remove local `InMemoryTaskRepository` class definition (lines 15-56)
- Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: Duplicate repository removed; tests pass

### Task 5.2: Update test_service_filtering.py
- Open `packages/tasky-tasks/tests/test_service_filtering.py`
- Add import: `from tasky_testing import InMemoryTaskRepository`
- Replace `MockTaskRepository` with `InMemoryTaskRepository`
- Refactor tests to populate repository state:
  - Create repository instance
  - Save tasks to repository before creating service
  - Pass repository to service
- Remove local `MockTaskRepository` class definition (lines 18-55)
- Run `uv run pytest packages/tasky-tasks/tests/test_service_filtering.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: Duplicate repository removed; tests refactored and passing

### Task 5.3: Migrate manual task creation to factories (optional, low priority)
- Search for patterns: `TaskModel(name="Test Task", details="Test details")`
- Identify test files with 5+ manual task creations
- Update to use `create_test_task()` factory
- Run tests for each updated file
- **Acceptance**: Boilerplate task creation reduced where beneficial

## Phase 6: Final Validation

### Task 6.1: Run complete test suite
- Run `uv run pytest`
- Verify all 577 tests pass
- Verify zero new test failures
- **Acceptance**: Complete test suite passes

### Task 6.2: Verify code quality
- Run `uv run ruff check packages/tasky-testing/`
- Run `uv run pyright packages/tasky-testing/`
- Fix any linting or type errors
- **Acceptance**: New package has zero quality issues

### Task 6.3: Verify coverage
- Run `uv run pytest --cov=packages/tasky-testing --cov-report=term-missing`
- Verify tasky-testing package has ≥80% coverage
- Add tests for any uncovered code paths
- **Acceptance**: Package meets coverage threshold

### Task 6.4: Verify line count reduction
- Check git diff for packages/tasky-tasks/tests/
- Verify removal of duplicate repositories (57 + 38 = 95 lines)
- Net line count should decrease even with new package
- **Acceptance**: Overall code duplication reduced

## Phase 7: Documentation and Finalization

### Task 7.1: Add package to architecture documentation
- Update project documentation to mention tasky-testing package
- Document its purpose as test utilities package
- Add to dependency graph
- **Acceptance**: Documentation reflects new package

### Task 7.2: Final verification
- Run complete validation suite:
  - `uv run pytest`
  - `uv run ruff check --fix`
  - `uv run pyright`
  - `uv run pytest --cov=packages --cov-fail-under=80`
- Verify all quality checks pass
- **Acceptance**: All quality gates passed; ready for review
