# Implementation Tasks: Enhance Task List Output

This document outlines the ordered implementation tasks for enhancing the task list output with status indicators, task IDs, and optional timestamp display. Tasks are designed to deliver user-visible improvements incrementally with validation at each step.

## Task Checklist

### Phase 1: Output Formatting (Foundation)

- [x] **Task 1.1**: Add status indicator symbols to task display
  - Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Map TaskStatus enum to symbols: PENDING → ○, COMPLETED → ✓, CANCELLED → ✗
  - Include status indicator in formatted output line
  - **Validation**: Status symbols display correctly for each status type

- [x] **Task 1.2**: Include task IDs in output
  - Update task display to show task.id (UUID format) before task name
  - Format: `○ {id} {name} - {details}`
  - Ensure UUIDs are displayed in standard format
  - **Validation**: Task IDs visible in list output

- [x] **Task 1.3**: Implement task sorting by status
  - Collect all tasks with their statuses
  - Sort in presentation layer: pending first, completed second, cancelled third
  - Within each status group, preserve original order or sort by ID
  - **Validation**: Task order matches spec (pending → completed → cancelled)

### Phase 2: Summary and Formatting

- [x] **Task 2.1**: Add task count summary line
  - Count total tasks displayed after list
  - Breakdown count by status: pending, completed, cancelled
  - Format: `Showing X tasks (Y pending, Z completed, W cancelled)`
  - Handle single task singular/plural correctly
  - **Validation**: Summary line displays with correct counts

- [x] **Task 2.2**: Handle empty task list
  - Detect when no tasks exist
  - Display clear message: "No tasks to display"
  - Do not display summary line when empty
  - **Validation**: Empty list shows appropriate message

- [x] **Task 2.3**: Format timestamps for --long flag
  - Add `--long` / `-l` option to task list command
  - When flag provided, display timestamps below each task
  - Show created_at and updated_at in ISO 8601 format
  - Indent timestamps with 2 spaces
  - **Validation**: Timestamps display correctly with --long flag

### Phase 3: Integration and Testing

- [x] **Task 3.1**: Ensure compatibility with existing filtering
  - Test enhanced output with `--status` filter (from add-task-filtering)
  - Verify summary counts reflect filtered results
  - Verify sorting applies to filtered results
  - **Validation**: Enhanced output works with status filtering

- [x] **Task 3.2**: Update help text
  - Update `tasky task list --help` to document output format
  - Document status indicators (○, ✓, ✗)
  - Document --long flag and its effect
  - Include example output in help text
  - **Validation**: Help text is clear and accurate

- [x] **Task 3.3**: Add unit tests for formatting
  - Create or update `packages/tasky-cli/tests/test_task_list_format.py`
  - Test status indicator mapping
  - Test UUID display
  - Test sorting order with mixed statuses
  - Test summary line count calculations
  - Test --long flag timestamp formatting
  - **Validation**: All formatting tests pass

- [x] **Task 3.4**: Add integration tests
  - Create or update `packages/tasky-cli/tests/test_list_integration.py`
  - End-to-end test with real task service
  - Test with mixed task statuses
  - Test --long flag with real timestamps
  - Test empty task list
  - Test with task filtering
  - **Validation**: Integration tests pass with real service

### Phase 4: Final Validation

- [x] **Task 4.1**: Manual smoke testing
  - Initialize fresh project: `uv run tasky project init`
  - Create tasks with different statuses: `uv run tasky task create <name> <details>`
  - Run `uv run tasky task list` and verify:
    - Status indicators display correctly
    - Task IDs are visible
    - Tasks are sorted (pending first)
    - Summary line shows correct counts
  - Test with `--long` flag and verify timestamps display
  - Test help text: `uv run tasky task list --help`
  - **Validation**: All manual tests pass

- [x] **Task 4.2**: Code quality and test coverage
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage for new formatting code
  - **Validation**: All tests pass (full suite)

- [x] **Task 4.3**: Run linting and formatting
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - **Validation**: Code passes all quality checks

## Notes

- **Dependencies**: Tasks within Phase 1 can run in parallel after Task 1.1 core setup
- **Phases**: Phases can overlap; Phase 2 formatting can start while Phase 1 sorting is in progress
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Rollback**: Each task is independently reversible if issues arise
- **Compatibility**: Enhanced output is intentionally backwards-incompatible (breaking change in presentation layer only)

## Estimated Duration

- Phase 1: 60 minutes (formatting + sorting)
- Phase 2: 45 minutes (summary + timestamps)
- Phase 3: 75 minutes (integration + testing)
- Phase 4: 45 minutes (validation + quality)

**Total**: ~4 hours

## Success Criteria

All tasks completed when:
1. Task list displays: status indicator + ID + name + details
2. Tasks are sorted by status (pending → completed → cancelled)
3. Summary line shows total and breakdown counts
4. `--long/-l` flag displays timestamps
5. All tests pass
6. Help text is documented
7. Code quality checks pass
