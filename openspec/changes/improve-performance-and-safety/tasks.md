## 1. JSON Backend Performance Optimization

- [x] 1.1 Refactor `find_tasks()` to apply filters to snapshots before model conversion
- [x] 1.2 Create `TaskFilter.matches_snapshot(snapshot: dict) -> bool` for efficient filtering
- [x] 1.3 Only convert filtered tasks to TaskModel (avoid 100% conversion)
- [x] 1.4 Benchmark: compare performance before/after with 10k tasks
- [x] 1.5 Run tests: `uv run pytest packages/tasky-storage/tests/test_json_repository.py -k find_tasks`
- [x] 1.6 Verify filtering behavior is identical (no regressions)

## 2. JSON Backend Atomic Writes

- [x] 2.1 Implement atomic write pattern: write to temp file, then atomic rename
- [x] 2.2 Update `JsonStorage.save()` to use atomic writes
- [x] 2.3 Ensure temp files are cleaned up on error
- [x] 2.4 Add tests for disk-full scenarios (verify no corruption)
- [x] 2.5 Test power-loss scenarios (simulate mid-write interruption)
- [x] 2.6 Run full test suite: `uv run pytest packages/tasky-storage/tests/`

## 3. Project Registry Pagination & Limits

- [x] 3.1 Add `MAX_REGISTRY_SIZE` constant (default: 10,000 projects)
- [x] 3.2 Implement lazy loading: load registry in batches instead of all at once
- [x] 3.3 Add pagination support to `ProjectRegistryService.list_projects(limit, offset)`
- [x] 3.4 Warn users when approaching registry size limit
- [x] 3.5 Add configuration option to adjust max registry size
- [x] 3.6 Test with 100k+ projects (memory usage should be bounded)

## 4. Import/Export Exception Handling

- [x] 4.1 Replace bare `except Exception` with specific exception types in import strategies
- [x] 4.2 Create custom exception type: `TaskImportError` for expected failures
- [x] 4.3 Let `TypeError`, `AttributeError`, `KeyError` propagate (programmer errors)
- [x] 4.4 Catch and log `TaskImportError` with task context (which task failed)
- [x] 4.5 Update user-facing error messages to include task details
- [x] 4.6 Run tests: `uv run pytest packages/tasky-tasks/tests/test_export.py -k import`

## 5. Registry Name Collision Diagnostics

- [x] 5.1 Replace bare `except Exception` with specific exception handling
- [x] 5.2 Log which disambiguation strategy was used and why (when adding suffix)
- [x] 5.3 Add metrics: how many collisions occurred, how they were resolved
- [x] 5.4 Provide user-friendly message if name disambiguation fails repeatedly
- [x] 5.5 Add tests for collision scenarios: 100 projects with same name
- [x] 5.6 Verify diagnostics appear in logs when debugging enabled

## 6. Performance & Reliability Testing

- [x] 6.1 Add benchmark test: JSON filtering with 10k tasks (measure improvement)
- [x] 6.2 Add stress test: create 1M tasks, verify no OOM errors
- [x] 6.3 Add atomic write test: simulate power-loss during save
- [x] 6.4 Add registry scale test: 100k projects, verify pagination works
- [x] 6.5 Run full test suite: `uv run pytest --cov=packages --cov-fail-under=80`
- [x] 6.6 Verify no performance regressions in other areas

## 7. Code Quality Validation

- [x] 7.1 Run `uv run pytest --cov=packages/tasky-storage --cov-report=html`
- [x] 7.2 Verify storage coverage improves or maintains ≥80%
- [x] 7.3 Run `uv run pytest --cov=packages/tasky-tasks --cov-report=html`
- [x] 7.4 Run `uv run ruff check --fix`
- [x] 7.5 Run `uv run pyright`
- [x] 7.6 Verify no bare `except Exception` remain in critical paths
