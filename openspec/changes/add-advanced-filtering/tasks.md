# Implementation Tasks: Add Advanced Task Filtering

This document outlines the ordered implementation tasks for adding advanced filtering capabilities (date range and text search). Tasks are designed to deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: Model & Protocol (Foundation)

- [ ] **Task 1.1**: Define `TaskFilter` model in `tasky-tasks`
  - Update `packages/tasky-tasks/src/tasky_tasks/models.py`
  - Add `TaskFilter` class with fields:
    - `statuses: list[TaskStatus] | None = None`
    - `created_after: datetime | None = None`
    - `created_before: datetime | None = None`
    - `name_contains: str | None = None`
  - Add `matches(task: TaskModel) -> bool` method implementing AND logic
  - **Validation**: Model type-checks successfully with all fields

- [ ] **Task 1.2**: Extend `TaskRepository` protocol with `find_tasks()` method
  - Update `packages/tasky-tasks/src/tasky_tasks/ports.py`
  - Add method signature: `def find_tasks(self, filter: TaskFilter) -> list[TaskModel]`
  - Include docstring explaining filter behavior and AND logic
  - **Validation**: Protocol type-checks successfully

- [ ] **Task 1.3**: Update `tasky-tasks` package exports
  - Update `packages/tasky-tasks/src/tasky_tasks/__init__.py`
  - Export `TaskFilter` for use by service and CLI
  - **Validation**: `from tasky_tasks import TaskFilter` works

- [ ] **Task 1.4**: Write unit tests for `TaskFilter` model
  - Create `packages/tasky-tasks/tests/test_filters.py`
  - Test `matches()` with single criteria (status only)
  - Test `matches()` with date range criteria
  - Test `matches()` with text search criteria
  - Test `matches()` with combined criteria (AND logic)
  - Test case-insensitive text search
  - Test date boundary conditions
  - Test with None values (criteria not specified)
  - **Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_filters.py -v`

### Phase 2: Service Layer Integration

- [ ] **Task 2.1**: Add `find_tasks()` method to `TaskService`
  - Update `packages/tasky-tasks/src/tasky_tasks/service.py`
  - Add method: `def find_tasks(self, filter: TaskFilter) -> list[TaskModel]`
  - Delegate to `self.repository.find_tasks(filter)`
  - Include logging at debug level
  - **Validation**: Service compiles without errors

- [ ] **Task 2.2**: Add convenience methods for common filter combinations
  - Add `get_tasks_by_date_range(after: datetime, before: datetime)` method
  - Add `search_tasks(text: str)` method
  - Add `get_pending_tasks_since(date: datetime)` convenience method
  - **Validation**: Service compiles and methods are callable

- [ ] **Task 2.3**: Write unit tests for service filtering
  - Update `packages/tasky-tasks/tests/test_filtering.py` or create new
  - Test `find_tasks()` with mock repository
  - Test convenience methods with various criteria
  - Test empty result sets
  - **Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_filtering.py -v`

### Phase 3: JSON Backend Implementation

- [ ] **Task 3.1**: Implement `find_tasks()` in `JsonTaskRepository`
  - Update `packages/tasky-storage/src/tasky_storage/backends/json/repository.py`
  - Implement in-memory filtering using `filter.matches(task)` method
  - Handle case-insensitive comparison in matches logic
  - Return empty list when no tasks match
  - **Validation**: Code compiles and type-checks

- [ ] **Task 3.2**: Write integration tests for JSON filtering
  - Update `packages/tasky-storage/tests/test_json_repository.py`
  - Test filtering with mixed task statuses and dates
  - Test date range filtering (before, after, both)
  - Test text search (case-insensitive)
  - Test combined criteria (AND logic)
  - Test with tasks missing creation dates (edge case)
  - Test with empty repository
  - **Validation**: Run `uv run pytest packages/tasky-storage/tests/test_json_repository.py -v`

### Phase 4: CLI Integration

- [ ] **Task 4.1**: Add `--created-after` option to `task list` command
  - Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add parameter: `created_after: str | None = typer.Option(None, "--created-after", help="...")`
  - Provide help text with ISO 8601 format example
  - **Validation**: Run `uv run tasky task list --help` and verify option appears

- [ ] **Task 4.2**: Add `--created-before` option to `task list` command
  - Add parameter: `created_before: str | None = typer.Option(None, "--created-before", help="...")`
  - Provide help text with ISO 8601 format example
  - **Validation**: Run `uv run tasky task list --help` and verify option appears

- [ ] **Task 4.3**: Add `--search` option to `task list` command
  - Add parameter: `search: str | None = typer.Option(None, "--search", help="...")`
  - Provide help text explaining case-insensitive search in name and details
  - **Validation**: Run `uv run tasky task list --help` and verify option appears

- [ ] **Task 4.4**: Implement date parsing and validation
  - Parse `--created-after` and `--created-before` as ISO 8601 dates
  - Validate date format and show helpful error for invalid dates
  - Example error: "Invalid date format: 'Jan 1'. Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)"
  - Use `datetime.fromisoformat()` for parsing
  - **Validation**: Manual testing with valid and invalid date formats

- [ ] **Task 4.5**: Build `TaskFilter` from CLI options
  - Convert CLI string options to `TaskFilter` object
  - Parse dates to `datetime` objects (at UTC midnight)
  - Handle status parameter (already supported)
  - Build filter with all non-None criteria
  - **Validation**: CLI parameters correctly translate to filter object

- [ ] **Task 4.6**: Integrate filtering with task service
  - Call `service.find_tasks(filter)` with constructed filter
  - Fall back to `service.get_all_tasks()` when no criteria provided
  - Handle empty result sets with clear messages
  - **Validation**: Manual testing with various filter combinations

- [ ] **Task 4.7**: Implement comprehensive error handling
  - Catch `ValueError` for invalid date formats
  - Show helpful error messages to users
  - Distinguish between invalid criteria and empty results
  - Exit with status code 1 for errors, 0 for success
  - **Validation**: Test error scenarios with helpful feedback

### Phase 5: Testing & Validation

- [ ] **Task 5.1**: Add end-to-end CLI tests for advanced filtering
  - Create/update `packages/tasky-cli/tests/test_advanced_filtering.py`
  - Test `--created-after` filter alone
  - Test `--created-before` filter alone
  - Test date range (`--created-after` AND `--created-before`)
  - Test `--search` filter alone
  - Test combined status and date filters
  - Test combined status and search filters
  - Test combined all three filters
  - Test invalid date format error
  - Test case-insensitive search
  - Test empty result messaging
  - **Validation**: Run `uv run pytest packages/tasky-cli/tests/test_advanced_filtering.py -v`

- [ ] **Task 5.2**: Test backward compatibility
  - Verify existing `--status` filtering still works
  - Verify `task list` without filters shows all tasks
  - Verify short form options work (`-s` for status)
  - Verify old command invocations produce identical output
  - **Validation**: Run full test suite: `uv run pytest`

- [ ] **Task 5.3**: Run full test suite and fix issues
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage meets ≥80% target
  - **Validation**: All tests pass (confirmed count)

- [ ] **Task 5.4**: Code quality checks
  - Run `uv run ruff check --fix` to fix linting issues
  - Run `uv run ruff format` to format code
  - Ensure no errors or warnings
  - **Validation**: Code passes all quality checks

- [ ] **Task 5.5**: Manual smoke testing
  - Initialize fresh project: `uv run tasky project init`
  - Create 5+ tasks with different names, details, statuses, and dates
  - Test each filter type individually
  - Test combinations of filters
  - Test error scenarios with invalid dates
  - Verify performance with larger task count (50+ tasks)
  - **Validation**: All filtering scenarios work correctly

- [ ] **Task 5.6**: Documentation & examples
  - Add filtering examples to CLI help text
  - Document the AND logic behavior
  - Note case-insensitive search behavior
  - Document date format requirements
  - Document error message guidance
  - **Validation**: Help text is clear and accurate

## Notes

- **Dependencies**: Tasks within each phase must follow sequence; phases can overlap
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Error Handling**: Prioritize user-friendly error messages with examples
- **Date Handling**: Always use UTC timezone for consistency
- **Case Sensitivity**: Search is case-insensitive; comparisons use `.lower()`

## Estimated Duration

- Phase 1: 45 minutes
- Phase 2: 30 minutes
- Phase 3: 45 minutes
- Phase 4: 90 minutes (CLI complexity)
- Phase 5: 60 minutes (testing)

**Total**: ~4 hours (plus 30 min buffer for debugging)
