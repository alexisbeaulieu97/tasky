# Implementation Tasks: Add Task Filtering

This document outlines the ordered implementation tasks for adding task filtering capabilities. Tasks are designed to deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: Protocol and Domain (Foundation)

- [ ] **Task 1.1**: Extend `TaskRepository` protocol with `get_tasks_by_status(status: TaskStatus)` method
  - Update `packages/tasky-tasks/src/tasky_tasks/ports.py`
  - Add method signature to protocol definition
  - Include docstring explaining filtering behavior
  - **Validation**: Protocol type-checks successfully

- [ ] **Task 1.2**: Add convenience methods to `TaskService`
  - Update `packages/tasky-tasks/src/tasky_tasks/service.py`
  - Add `get_tasks_by_status(status: TaskStatus)` delegating to repository
  - Add `get_pending_tasks()` calling `get_tasks_by_status(TaskStatus.PENDING)`
  - Add `get_completed_tasks()` calling `get_tasks_by_status(TaskStatus.COMPLETED)`
  - Add `get_cancelled_tasks()` calling `get_tasks_by_status(TaskStatus.CANCELLED)`
  - **Validation**: Service compiles without errors

- [ ] **Task 1.3**: Write unit tests for service filtering methods
  - Create `packages/tasky-tasks/tests/test_filtering.py`
  - Test `get_tasks_by_status()` with mock repository
  - Test convenience methods call correct status values
  - Test empty result sets
  - Test filtering returns only matching status
  - **Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_filtering.py -v`

### Phase 2: JSON Backend Implementation

- [ ] **Task 2.1**: Implement `get_tasks_by_status()` in `JsonTaskRepository`
  - Update `packages/tasky-storage/src/tasky_storage/backends/json/repository.py`
  - Implement in-memory filtering using list comprehension
  - Return empty list when document doesn't exist
  - Handle conversion from snapshot to TaskModel correctly
  - **Validation**: Code compiles and type-checks

- [ ] **Task 2.2**: Write integration tests for JSON filtering
  - Update `packages/tasky-storage/tests/test_json_repository.py`
  - Test filtering with mixed task statuses
  - Test filtering when no tasks match
  - Test filtering returns correct tasks
  - Test filtering with empty repository
  - Test filtering preserves task data integrity
  - **Validation**: Run `uv run pytest packages/tasky-storage/tests/test_json_repository.py::TestJsonTaskRepository::test_get_tasks_by_status -v`

### Phase 3: CLI Integration

- [ ] **Task 3.1**: Add `--status` option to `task list` command
  - Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add `status: Optional[str]` parameter with `typer.Option`
  - Provide help text and examples
  - Support both `--status` and `-s` short form
  - Preserve existing behavior when option not provided
  - **Validation**: Run `uv run tasky task list --help` and verify option appears

- [ ] **Task 3.2**: Implement status validation and filtering logic
  - Validate status string against TaskStatus enum values
  - Show helpful error message for invalid status values
  - Call `service.get_tasks_by_status()` when status provided
  - Call `service.get_all_tasks()` when status not provided
  - **Validation**: Manual testing with valid and invalid status values

- [ ] **Task 3.3**: Format filtered results consistently
  - Ensure filtered output matches existing format
  - Add status indicator in output (optional enhancement)
  - Handle empty result sets with clear message
  - **Validation**: Run `uv run tasky task list --status pending` and verify output

### Phase 4: Testing and Documentation

- [ ] **Task 4.1**: Add end-to-end CLI tests
  - Create test scenarios in `packages/tasky-cli/tests/test_filtering.py`
  - Test filtering with real JSON backend
  - Test invalid status error handling
  - Test empty results messaging
  - Test short and long option forms
  - **Validation**: Run `uv run pytest packages/tasky-cli/tests/ -k filtering -v`

- [ ] **Task 4.2**: Run full test suite and fix issues
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage meets ≥80% target
  - **Validation**: All tests pass with adequate coverage

- [ ] **Task 4.3**: Update documentation
  - Add filtering examples to CLI help text
  - Document the filtering behavior in code comments
  - Note future enhancement opportunities
  - **Validation**: Documentation is clear and accurate

### Phase 5: Final Validation

- [ ] **Task 5.1**: Manual smoke testing
  - Initialize fresh project with `uv run tasky project init`
  - Create tasks with different statuses
  - Test all filtering variations
  - Verify performance with larger task count
  - **Validation**: All filtering scenarios work correctly

- [ ] **Task 5.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - **Validation**: Code passes all quality checks

## Notes

- **Dependencies**: Tasks must be completed sequentially within each phase
- **Parallelization**: Phases 1 and 2 can overlap once protocols are defined
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Rollback**: Each task is independently reversible if issues arise

## Estimated Duration

- Phase 1: 30 minutes
- Phase 2: 45 minutes
- Phase 3: 45 minutes
- Phase 4: 30 minutes
- Phase 5: 30 minutes

**Total**: ~3 hours
