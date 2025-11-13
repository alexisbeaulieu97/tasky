# Implementation Tasks: Add Task Update Command

This document outlines the ordered implementation tasks for adding the `tasky task update` CLI command. Tasks are designed to deliver user-visible functionality with validation at each step.

## Task Checklist

### Phase 1: CLI Command Implementation

- [x] **Task 1.1**: Add `update_command()` function to `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add function signature: `def update_command(task_id: str, name: Optional[str] = None, details: Optional[str] = None) -> None:`
  - Use `typer.echo()` for output
  - Include docstring explaining the command
  - **Validation**: Function compiles without syntax errors

- [x] **Task 1.2**: Implement validation for required field flags
  - Validate that at least one of `--name` or `--details` is provided
  - Display helpful error message if neither is provided
  - Exit with status code 1 on validation failure
  - **Validation**: Error shown when neither flag is provided

- [x] **Task 1.3**: Implement service integration in update command
  - Create task service instance using `create_task_service()`
  - Call `service.get_task(task_id)` to retrieve the current task
  - Modify only the specified fields in the retrieved task
  - Call `service.update_task(modified_task)` to persist changes
  - Capture updated `TaskModel` instance
  - **Validation**: Service calls execute without errors

- [x] **Task 1.4**: Format and display updated task output
  - Display task ID prominently
  - Display task name
  - Display task details
  - Display status
  - Display modification/update timestamp
  - Use consistent formatting with existing commands
  - **Validation**: Output is human-readable and informative

- [x] **Task 1.5**: Add command registration to CLI
  - Import `update_command` in `packages/tasky-cli/src/tasky_cli/commands/__init__.py`
  - Register command in task subcommand group
  - Verify `tasky task update --help` shows the command
  - **Validation**: `uv run tasky task update --help` displays help text

### Phase 2: Argument Validation and Error Handling

- [x] **Task 2.1**: Add validation for required TASK_ID argument
  - TASK_ID parameter is positional and required
  - Typer automatically validates required positional args
  - **Validation**: Running without TASK_ID shows error

- [x] **Task 2.2**: Add validation for optional flags
  - `--name` and `--details` are optional but at least one is required
  - Clear error message if neither flag is provided
  - **Validation**: Error shown when no flags provided

- [x] **Task 2.3**: Implement error handling for service failures
  - Catch exceptions from `service.get_task()` (task not found)
  - Catch exceptions from `service.update_task()` (storage errors)
  - Display helpful error messages
  - Exit with non-zero status on error
  - Follow existing error handling patterns
  - **Validation**: Invalid operations show clear error messages

- [x] **Task 2.4**: Add argument help text and examples
  - Provide clear descriptions for TASK_ID parameter
  - Provide clear descriptions for `--name` and `--details` flags
  - Include usage examples in help text
  - Show example command invocations
  - **Validation**: `uv run tasky task update --help` shows helpful text

### Phase 3: Testing

- [x] **Task 3.1**: Write unit tests for update command
  - Create `packages/tasky-cli/tests/test_task_update.py`
  - Test successful update with name only
  - Test successful update with details only
  - Test successful update with both name and details
  - Test with different name and details strings
  - **Validation**: Tests pass with `uv run pytest packages/tasky-cli/tests/test_task_update.py -v`

- [x] **Task 3.2**: Write error case tests
  - Test error when no TASK_ID provided
  - Test error when neither `--name` nor `--details` provided
  - Test error when task ID does not exist
  - Test with invalid task ID format
  - Test error message clarity for each case
  - **Validation**: All error cases handled gracefully

- [x] **Task 3.3**: Write integration tests with storage backends
  - Test update command with JSON backend
  - Test update command with SQLite backend
  - Create task, update it, verify changes persisted
  - Retrieve updated task with `tasky task list` and verify changes
  - Test updating name, details, and both fields
  - **Validation**: `uv run pytest packages/tasky-cli/tests/ -k "update" -v`

- [x] **Task 3.4**: Verify field isolation in updates
  - Create task with name and details
  - Update only name and verify details unchanged
  - Update only details and verify name unchanged
  - Update both and verify both changed
  - **Validation**: Unmodified fields remain unchanged

### Phase 4: Validation and Polish

- [x] **Task 4.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify no tests broken by new command
  - **Validation**: All tests pass

- [x] **Task 4.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors or warnings
  - **Validation**: No linting issues

- [x] **Task 4.3**: Manual smoke testing
  - Initialize fresh project with `uv run tasky project init`
  - Create a task: `uv run tasky task create "Original name" "Original details"`
  - Copy the task ID from output
  - Update name only: `uv run tasky task update <id> --name "Updated name"`
  - Verify output shows updated name and original details
  - Update details only: `uv run tasky task update <id> --details "Updated details"`
  - Verify output shows original name (unchanged) and updated details
  - Update both: `uv run tasky task update <id> --name "Final name" --details "Final details"`
  - List tasks and verify all changes persisted
  - Test error case: `uv run tasky task update <id>` (no flags - should error)
  - Test error case: `uv run tasky task update nonexistent-id --name "Test"` (task not found)
  - **Validation**: Command works end-to-end

### Phase 5: Documentation

- [x] **Task 5.1**: Update command documentation
  - Add update command example to help text
  - Provide usage scenarios in docstring
  - Document expected output format
  - Show examples of updating different fields
  - **Validation**: Help text is clear and complete

- [x] **Task 5.2**: Add code comments
  - Document key implementation decisions
  - Explain error handling approach
  - Note validation logic for field flags
  - Document field isolation strategy
  - **Validation**: Code is well-commented

## Notes

- **Dependencies**: Phases must be completed sequentially
- **Testing Strategy**: Test at command layer (unit) and integration layers
- **Error Handling**: Follow patterns from existing `task list` and `task create` commands
- **Output Format**: Match style of existing commands for consistency
- **Field Isolation**: Critical to verify that unmodified fields remain unchanged when persisting updates

## Estimated Duration

- Phase 1: 50 minutes
- Phase 2: 35 minutes
- Phase 3: 50 minutes
- Phase 4: 25 minutes
- Phase 5: 15 minutes

**Total**: ~2.75 hours
