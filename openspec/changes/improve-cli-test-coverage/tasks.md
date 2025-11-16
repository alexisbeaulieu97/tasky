## 1. Error Handler Path Testing

- [ ] 1.1 Add tests for `_handle_task_domain_error` with each exception type (NotFound, Validation, InvalidState)
- [ ] 1.2 Add tests for `_handle_storage_error` with each storage error condition
- [ ] 1.3 Add tests for `_handle_registry_error` with missing/corrupted registry
- [ ] 1.4 Add tests for `_handle_generic_error` with unexpected exception types
- [ ] 1.5 Verify error messages are user-friendly (no Python stack traces shown)
- [ ] 1.6 Verify exit codes are correct (1 for user error, 2 for internal error)

## 2. Task Creation Command Error Cases

- [ ] 2.1 Add test: missing task name (validation error)
- [ ] 2.2 Add test: empty name string
- [ ] 2.3 Add test: invalid priority value
- [ ] 2.4 Add test: invalid due date format
- [ ] 2.5 Add test: storage write fails (disk full)
- [ ] 2.6 Add test: project not found

## 3. Task Update Command Error Cases

- [ ] 3.1 Add test: task not found (ID doesn't exist)
- [ ] 3.2 Add test: invalid task ID format (non-UUID)
- [ ] 3.3 Add test: invalid status transition
- [ ] 3.4 Add test: empty update (no fields specified)
- [ ] 3.5 Add test: update with invalid due date
- [ ] 3.6 Add test: concurrent modification during update

## 4. Task List Command Edge Cases

- [ ] 4.1 Add test: list with no tasks in project (empty database)
- [ ] 4.2 Add test: list with 1000+ tasks (performance + pagination)
- [ ] 4.3 Add test: list with all filters combined (status + search + date range)
- [ ] 4.4 Add test: list output formatting with long task names (>100 chars)
- [ ] 4.5 Add test: list with special characters in task details

## 5. Import Command Edge Cases

- [ ] 5.1 Add test: import from empty file (0 bytes)
- [ ] 5.2 Add test: import with malformed JSON (syntax error)
- [ ] 5.3 Add test: import with missing required fields (incomplete task)
- [ ] 5.4 Add test: import strategy=skip (duplicate task IDs)
- [ ] 5.5 Add test: import strategy=merge (resolve conflicts)
- [ ] 5.6 Add test: import with 10,000 tasks (memory + performance)
- [ ] 5.7 Add test: import creates backup before executing
- [ ] 5.8 Add test: dry-run mode doesn't modify database

## 6. Export Command Edge Cases

- [ ] 6.1 Add test: export with no filters (all tasks)
- [ ] 6.2 Add test: export with filters (status + search)
- [ ] 6.3 Add test: export creates valid, re-importable file
- [ ] 6.4 Add test: export with 10,000 tasks (file size + performance)
- [ ] 6.5 Add test: export file has proper JSON formatting
- [ ] 6.6 Add test: export with special characters in task content

## 7. Input Validation Integration

- [ ] 7.1 Add tests for new TaskIdValidator integration
- [ ] 7.2 Add tests for new DateValidator integration
- [ ] 7.3 Add tests for new StatusValidator integration
- [ ] 7.4 Add tests for new PriorityValidator integration
- [ ] 7.5 Verify validators are called before service invocation

## 8. Validation & Coverage

- [ ] 8.1 Run `uv run pytest --cov=packages/tasky-cli --cov-fail-under=80`
- [ ] 8.2 Generate coverage report: `uv run pytest --cov=packages/tasky-cli --cov-report=html`
- [ ] 8.3 Verify tasks.py coverage ≥80% (currently 69%)
- [ ] 8.4 Run `uv run ruff check --fix`
- [ ] 8.5 Run `uv run pyright`
