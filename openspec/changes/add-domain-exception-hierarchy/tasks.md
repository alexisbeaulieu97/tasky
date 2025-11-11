# Tasks: Domain Exception Hierarchy

**Change ID**: `add-domain-exception-hierarchy`  
**Status**: Not Started

## Task Checklist

### Phase 1: Exception Foundation (Domain Layer)

- [ ] **1.1**: Create `packages/tasky-tasks/src/tasky_tasks/exceptions.py`
  - Define `TaskDomainError` base class with docstring
  - Define `TaskNotFoundError` with `task_id` attribute
  - Define `TaskValidationError` with `message` attribute
  - Define `InvalidStateTransitionError` with `task_id`, `from_status`, `to_status` attributes
  - Implement `__init__` methods with proper attribute assignment
  - Implement `__str__` methods for human-readable messages
  - Implement `__repr__` methods for debugging
  - Add comprehensive docstrings for each exception class

- [ ] **1.2**: Update `packages/tasky-tasks/src/tasky_tasks/__init__.py`
  - Export `TaskDomainError`
  - Export `TaskNotFoundError`
  - Export `TaskValidationError`
  - Export `InvalidStateTransitionError`
  - Add exports to `__all__` list

- [ ] **1.3**: Create `packages/tasky-tasks/tests/test_exceptions.py`
  - Test `TaskDomainError` base class instantiation
  - Test `TaskNotFoundError` with task_id context
  - Test `TaskValidationError` with message
  - Test `InvalidStateTransitionError` with full context
  - Test exception string representations
  - Test exception repr for debugging
  - Test exception inheritance hierarchy
  - Test exception attribute access

### Phase 2: Service Layer Integration

- [ ] **2.1**: Update `packages/tasky-tasks/src/tasky_tasks/service.py`
  - Import exception classes from `tasky_tasks.exceptions`
  - Update `get_task()` to raise `TaskNotFoundError` when task not found
  - Update `delete_task()` to raise `TaskNotFoundError` when task not found
  - Add docstrings documenting raised exceptions
  - Add type hints for return types (remove `| None` where exceptions handle failures)

- [ ] **2.2**: Create `packages/tasky-tasks/tests/test_service_exceptions.py`
  - Test `get_task()` raises `TaskNotFoundError` for non-existent task
  - Test `delete_task()` raises `TaskNotFoundError` for non-existent task
  - Test exception includes correct task_id context
  - Test successful operations don't raise exceptions
  - Test exception messages are descriptive

- [ ] **2.3**: Update existing service tests
  - Review `packages/tasky-tasks/tests/test_service.py` (if exists)
  - Update tests expecting `None` returns to expect exceptions
  - Add exception assertions where appropriate

### Phase 3: CLI Error Handling

- [ ] **3.1**: Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Import exception classes from `tasky_tasks`
  - Add try-except blocks to all task commands
  - Handle `TaskNotFoundError` with user-friendly message
  - Handle `TaskValidationError` with user-friendly message
  - Handle `InvalidStateTransitionError` with user-friendly message
  - Use `typer.echo(..., err=True)` for error messages
  - Raise `typer.Exit(1)` for domain errors
  - Raise `typer.Exit(3)` for storage errors

- [ ] **3.2**: Implement error message formatting
  - Create error message templates for each exception type
  - Extract context (task_id, status) from exceptions
  - Format messages as "Error: <description>"
  - Keep messages concise and actionable
  - Add suggestions where appropriate

- [ ] **3.3**: Add verbose mode support (optional)
  - Check if verbose flag exists from existing implementation
  - If verbose, display full traceback
  - If not verbose, display only user message
  - Ensure verbose mode works with all error types

- [ ] **3.4**: Create `packages/tasky-cli/tests/test_error_handling.py`
  - Test each command handles `TaskNotFoundError` correctly
  - Test error messages are formatted properly
  - Test exit codes are correct (1 for domain, 3 for storage)
  - Test errors go to stderr
  - Test verbose mode shows stack traces (if implemented)

### Phase 4: Integration Testing

- [ ] **4.1**: Create integration test scenarios
  - Test end-to-end error flow: repository → service → CLI
  - Test task not found scenario with real repository
  - Test validation error scenario
  - Test multiple commands handle errors consistently
  - Verify no Python exceptions visible in CLI output

- [ ] **4.2**: Update existing CLI tests
  - Review existing tests in `packages/tasky-cli/tests/`
  - Update tests that may be affected by exception changes
  - Add assertions for error cases
  - Ensure tests verify exit codes

### Phase 5: Documentation and Validation

- [ ] **5.1**: Update code documentation
  - Add docstring examples showing exception usage
  - Document error propagation strategy in module docstrings
  - Update README files if needed
  - Add type hints consistently

- [ ] **5.2**: Run validation
  - Execute `uv run pytest` to ensure all tests pass
  - Execute `uv run ruff check --fix` to ensure linting passes
  - Execute `openspec validate add-domain-exception-hierarchy --strict`
  - Fix any validation issues

- [ ] **5.3**: Manual testing
  - Test each CLI command with invalid inputs
  - Verify error messages are clear and helpful
  - Check exit codes using `echo $?` after commands
  - Test in both normal and verbose modes
  - Verify no crashes or unexpected exceptions

---

## Dependencies

- **Requires**: None (independent change)
- **Enables**: `add-task-state-machine` (User Story 4)
- **Related**: `add-configurable-storage-backends` (for `ProjectNotFoundError` pattern)

---

## Validation Commands

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=tasky_tasks --cov=tasky_cli

# Run linting
uv run ruff check --fix

# Validate OpenSpec
openspec validate add-domain-exception-hierarchy --strict

# Manual CLI testing
uv run tasky task show non-existent-id
echo $?  # Should be 1

uv run tasky task delete non-existent-id
echo $?  # Should be 1
```

---

## Acceptance Criteria

- ✅ All domain exceptions include relevant context attributes
- ✅ Service methods raise appropriate exceptions instead of returning `None`
- ✅ CLI displays user-friendly error messages (no stack traces)
- ✅ CLI exits with appropriate codes (1=domain, 3=storage)
- ✅ Error handling is consistent across all commands
- ✅ All tests pass (`uv run pytest`)
- ✅ Linting passes (`uv run ruff check`)
- ✅ OpenSpec validation passes (`openspec validate --strict`)

---

## Notes

- Keep exception messages domain-focused (avoid storage implementation details)
- Preserve exception context through chaining where appropriate
- Test both success and failure paths for all service methods
- Ensure CLI error messages are understandable by non-developers
- Consider future: logging integration for error tracking
