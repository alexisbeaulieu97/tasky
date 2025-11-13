# Implementation Tasks: Add Task Create Command

This document outlines the ordered implementation tasks for adding the `tasky task create` CLI command. Tasks are designed to deliver user-visible functionality with validation at each step.

## Task Checklist

### Phase 1: CLI Command Implementation

- [x] **Task 1.1**: Add `create_command()` function to `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add function signature: `def create_command(name: str, details: str) -> None:`
  - Use `typer.echo()` for output
  - Include docstring explaining the command
  - **Validation**: Function compiles without syntax errors

- [x] **Task 1.2**: Implement service integration in create command
  - Create task service instance using `create_task_service()`
  - Call `service.create_task(name, details)`
  - Capture returned `TaskModel` instance
  - **Validation**: Service call executes without errors

- [x] **Task 1.3**: Format and display created task output
  - Display task ID prominently
  - Display task name
  - Display task details
  - Display creation timestamp
  - Display status (should be PENDING)
  - Use consistent formatting with existing commands
  - **Validation**: Output is human-readable and informative

- [x] **Task 1.4**: Add command registration to CLI
  - Import `create_command` in `packages/tasky-cli/src/tasky_cli/commands/__init__.py`
  - Register command in task subcommand group
  - Verify `tasky task create --help` shows the command
  - **Validation**: `uv run tasky task create --help` displays help text

### Phase 2: Argument Validation and Error Handling

- [x] **Task 2.1**: Add validation for required arguments
  - NAME parameter is positional and required
  - DETAILS parameter is positional and required
  - Typer automatically validates required positional args
  - **Validation**: Running without arguments shows error

- [x] **Task 2.2**: Implement error handling for service failures
  - Catch exceptions from `service.create_task()`
  - Display helpful error messages
  - Exit with non-zero status on error
  - Follow existing error handling patterns
  - **Validation**: Invalid operations show clear error messages

- [x] **Task 2.3**: Add argument help text and examples
  - Provide clear descriptions for NAME and DETAILS parameters
  - Include usage examples in help text
  - Show example command invocation
  - **Validation**: `uv run tasky task create --help` shows helpful text

### Phase 3: Testing

- [x] **Task 3.1**: Write unit tests for create command
  - Create `packages/tasky-cli/tests/test_task_create.py`
  - Test successful task creation
  - Test output formatting
  - Test with different name and details strings
  - **Validation**: Tests pass with `uv run pytest packages/tasky-cli/tests/test_task_create.py -v`

- [x] **Task 3.2**: Write integration tests with JSON backend
  - Test create command with real task service
  - Verify task is actually persisted
  - Test retrieving created task with `tasky task list`
  - Test timestamp and ID assignment
  - **Validation**: `uv run pytest packages/tasky-cli/tests/ -k "create" -v`

- [x] **Task 3.3**: Write error case tests
  - Test with missing NAME argument
  - Test with missing DETAILS argument
  - Test with service failures
  - Test error message clarity
  - **Validation**: All error cases handled gracefully

### Phase 4: Validation and Polish

- [x] **Task 4.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify no tests broken by new command
  - **Validation**: All tests pass (200+ tests)

- [x] **Task 4.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors or warnings
  - **Validation**: No linting issues

- [x] **Task 4.3**: Manual smoke testing
  - Initialize fresh project with `uv run tasky project init`
  - Create a task: `uv run tasky task create "Test task" "Test details"`
  - Verify output shows ID, name, status, and timestamp
  - List tasks: `uv run tasky task list` and verify created task appears
  - Test with different task names and details
  - **Validation**: Command works end-to-end

### Phase 5: Documentation

- [x] **Task 5.1**: Update command documentation
  - Add create command example to help text
  - Provide usage scenarios in docstring
  - Document expected output format
  - **Validation**: Help text is clear and complete

- [x] **Task 5.2**: Add code comments
  - Document key implementation decisions
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
