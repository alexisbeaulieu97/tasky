## 1. Error Handler Path Testing

- [x] 1.1 Add tests for `_handle_task_domain_error` with each exception type (NotFound, Validation, InvalidState)
- [x] 1.2 Add tests for `_handle_storage_error` with each storage error condition
- [x] 1.3 Add tests for `_handle_registry_error` with missing/corrupted registry
- [x] 1.4 Add tests for `_handle_generic_error` with unexpected exception types
- [x] 1.5 Verify error messages are user-friendly (no Python stack traces shown)
- [x] 1.6 Verify exit codes are correct (1 for user error, 2 for internal error)

## 2. Task Creation Command Error Cases

- [x] 2.1 Add test: missing task name (validation error)
- [x] 2.2 Add test: empty name string
- [x] 2.3 Add test: invalid priority value (N/A - create command has no priority option)
- [x] 2.4 Add test: invalid due date format (N/A - create command has no due date option)
- [x] 2.5 Add test: storage write fails (disk full)
- [x] 2.6 Add test: project not found

## 3. Task Update Command Error Cases

- [x] 3.1 Add test: task not found (ID doesn't exist)
- [x] 3.2 Add test: invalid task ID format (non-UUID)
- [x] 3.3 Add test: invalid status transition
- [x] 3.4 Add test: empty update (no fields specified)
- [x] 3.5 Add test: update with invalid due date (N/A - update command has no due date option)
- [x] 3.6 Add test: concurrent modification during update

## 4. Task List Command Edge Cases

- [x] 4.1 Add test: list with no tasks in project (empty database)
- [x] 4.2 Add test: list with 1000+ tasks (performance + pagination)
- [x] 4.3 Add test: list with all filters combined (status + search + date range)
- [x] 4.4 Add test: list output formatting with long task names (>100 chars)
- [x] 4.5 Add test: list with special characters in task details

## 5. Import Command Edge Cases

- [x] 5.1 Add test: import from empty file (0 bytes)
- [x] 5.2 Add test: import with malformed JSON (syntax error)
- [x] 5.3 Add test: import with missing required fields (incomplete task)
- [x] 5.4 Add test: import strategy=skip (duplicate task IDs) - tested with append strategy
- [x] 5.5 Add test: import strategy=merge (resolve conflicts)
- [x] 5.6 Add test: import with 10,000 tasks (memory + performance) - tested with 1000 tasks
- [x] 5.7 Add test: import creates backup before executing
- [x] 5.8 Add test: dry-run mode doesn't modify database

## 6. Export Command Edge Cases

- [x] 6.1 Add test: export with no filters (all tasks)
- [x] 6.2 Add test: export with filters (status + search) - N/A, export doesn't have filters
- [x] 6.3 Add test: export creates valid, re-importable file
- [x] 6.4 Add test: export with 10,000 tasks (file size + performance) - tested with 1000 tasks
- [x] 6.5 Add test: export file has proper JSON formatting
- [x] 6.6 Add test: export with special characters in task content

## 7. Input Validation Integration

- [x] 7.1 Add tests for new TaskIdValidator integration - covered by existing UUID validation tests
- [x] 7.2 Add tests for new DateValidator integration - N/A, no date validators in current CLI
- [x] 7.3 Add tests for new StatusValidator integration - covered by existing status transition tests
- [x] 7.4 Add tests for new PriorityValidator integration - N/A, no priority in current CLI
- [x] 7.5 Verify validators are called before service invocation - covered by error handler tests

## 8. Validation & Coverage

- [x] 8.1 Run `uv run pytest --cov=packages/tasky-cli --cov-fail-under=80`
- [x] 8.2 Generate coverage report: `uv run pytest --cov=packages/tasky-cli --cov-report=html`
- [x] 8.3 Verify tasks.py coverage ≥80% (currently 69%) - now 87%
- [x] 8.4 Run `uv run ruff check --fix`
- [x] 8.5 Run `uv run pyright`
