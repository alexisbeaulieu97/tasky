# Implementation Tasks: Add Task Show Command

This document outlines the ordered implementation tasks for adding the `tasky task show TASK_ID` CLI command. Tasks are designed to deliver user-visible functionality with validation at each step.

## Task Checklist

### Phase 1: CLI Command Implementation

- [x] **Task 1.1**: Add `show_command()` function to `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add function signature: `def show_command(task_id: str) -> None:`
  - Use `typer.echo()` for output
  - Include docstring explaining the command
  - **Validation**: Function compiles without syntax errors

- [x] **Task 1.2**: Implement service integration in show command
  - Parse task_id string to UUID using `uuid.UUID()`
  - Create task service instance using `create_task_service()`
  - Call `service.get_task(task_id_uuid)`
  - Capture returned `TaskModel` instance
  - **Validation**: Service call executes without errors for valid UUIDs

- [x] **Task 1.3**: Format and display task output
  - Display task ID
  - Display task name
  - Display task details
  - Display task status
  - Display created timestamp
  - Display updated timestamp
  - Use consistent formatting with existing commands
  - **Validation**: Output is human-readable and informative

- [x] **Task 1.4**: Add command registration to CLI
  - Import `show_command` in `packages/tasky-cli/src/tasky_cli/commands/__init__.py`
  - Register command in task subcommand group
  - Verify `tasky task show --help` shows the command
  - **Validation**: `uv run tasky task show --help` displays help text

### Phase 2: Argument Validation and Error Handling

- [x] **Task 2.1**: Add validation for required TASK_ID argument
  - TASK_ID parameter is positional and required
  - Validate that TASK_ID is a valid UUID format
  - Catch `ValueError` from invalid UUID parsing
  - Display helpful error message for invalid UUID format
  - **Validation**: Running without TASK_ID shows error; invalid UUID shows format error

- [x] **Task 2.2**: Implement error handling for missing tasks
  - Catch exceptions from `service.get_task()` (likely `TaskNotFound` or similar)
  - Display helpful error message when task does not exist
  - Exit with non-zero status on error
  - Include the provided task ID in error message
  - Follow existing error handling patterns
  - **Validation**: Non-existent task ID shows clear "task not found" message

- [x] **Task 2.3**: Add argument help text and examples
  - Provide clear description for TASK_ID parameter
  - Include usage examples in help text
  - Show example with valid UUID
  - Explain what the command does
  - **Validation**: `uv run tasky task show --help` shows helpful text

### Phase 3: Testing

- [x] **Task 3.1**: Write unit tests for show command
  - Create `packages/tasky-cli/tests/test_task_show.py`
  - Test successful task retrieval with valid task ID
  - Test output formatting
  - Test with different task details (long names, special characters)
  - **Validation**: Tests pass with `uv run pytest packages/tasky-cli/tests/test_task_show.py -v`

- [x] **Task 3.2**: Write integration tests with real service
  - Test show command with real task service
  - Create a task, then show it and verify all fields
  - Verify timestamp accuracy and formatting
  - Test retrieval of same task ID multiple times
  - **Validation**: `uv run pytest packages/tasky-cli/tests/ -k "show" -v`

- [x] **Task 3.3**: Write error case tests
  - Test with missing TASK_ID argument
  - Test with invalid UUID format
  - Test with non-existent task ID (after creating other tasks)
  - Test error message clarity and helpfulness
  - **Validation**: All error cases handled gracefully

### Phase 4: Validation and Polish

- [x] **Task 4.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify no tests broken by new command
  - **Validation**: All tests pass (263 tests)

- [x] **Task 4.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors or warnings
  - **Validation**: No linting issues

- [x] **Task 4.3**: Manual smoke testing
  - Initialize fresh project with `uv run tasky project init`
  - Create a task: `uv run tasky task create "Test task" "Test details"`
  - Copy the returned task ID
  - Show the task: `uv run tasky task show <task-id>`
  - Verify output shows ID, name, details, status, and timestamps
  - Test with invalid UUID format and verify error message
  - Test with non-existent task ID and verify error message
  - **Validation**: Command works end-to-end

### Phase 5: Documentation

- [x] **Task 5.1**: Update command documentation
  - Add show command example to help text
  - Provide usage scenarios in docstring
  - Document expected output format
  - Document error conditions
  - **Validation**: Help text is clear and complete

- [x] **Task 5.2**: Add code comments
  - Document UUID validation logic
  - Explain error handling approach
  - Note any assumptions or constraints
  - **Validation**: Code is well-commented

## Notes

- **Dependencies**: Phases must be completed sequentially
- **Testing Strategy**: Test at command layer (unit) and integration layers
- **Error Handling**: Follow patterns from existing `task list` command
- **Output Format**: Match style of existing commands for consistency

## Estimated Duration

- Phase 1: 45 minutes
- Phase 2: 30 minutes
- Phase 3: 45 minutes
- Phase 4: 20 minutes
- Phase 5: 15 minutes

**Total**: ~2.5 hours
