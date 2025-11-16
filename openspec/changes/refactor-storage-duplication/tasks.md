## 1. Shared Utility Module Creation

- [ ] 1.1 Create `packages/tasky-storage/src/tasky_storage/shared.py`
- [ ] 1.2 Extract snapshot conversion logic to `convert_snapshot_to_task(snapshot, TaskModel) -> TaskModel`
- [ ] 1.3 Implement unified error handling: `ConversionError` wraps snapshot validation failures
- [ ] 1.4 Add comprehensive docstring explaining snapshot format and conversion requirements
- [ ] 1.5 Write unit tests for shared utility functions
- [ ] 1.6 Verify utility works with both JSON and SQLite snapshot formats

## 2. Serialization Standardization

- [ ] 2.1 Update JSON backend to use `task.model_dump(mode="json")` instead of custom encoder
- [ ] 2.2 Remove `TaskyJSONEncoder` class from JSON backend if no longer needed
- [ ] 2.3 Verify JSON output is identical before/after (byte-for-byte comparison)
- [ ] 2.4 Run JSON backend tests: `uv run pytest packages/tasky-storage/tests/test_json_repository.py`
- [ ] 2.5 Verify datetime/enum serialization is consistent across backends

## 3. JSON Backend Refactoring

- [ ] 3.1 Replace `_snapshot_to_task` with call to shared utility
- [ ] 3.2 Update error handling to use shared exceptions
- [ ] 3.3 Remove duplicate error handling code from JSON repository
- [ ] 3.4 Run all tests: `uv run pytest packages/tasky-storage/tests/test_json_repository.py`
- [ ] 3.5 Verify coverage doesn't decrease

## 4. SQLite Backend Refactoring

- [ ] 4.1 Replace `_snapshot_to_task` with call to shared utility
- [ ] 4.2 Update error handling to use shared exceptions
- [ ] 4.3 Remove duplicate error handling code from SQLite repository
- [ ] 4.4 Run all tests: `uv run pytest packages/tasky-storage/tests/test_sqlite_repository.py`
- [ ] 4.5 Verify coverage doesn't decrease

## 5. Cross-Backend Validation

- [ ] 5.1 Create test comparing JSON and SQLite serialization (identical output)
- [ ] 5.2 Run integration tests with both backends: `uv run pytest tests/`
- [ ] 5.3 Verify no behavioral changes between before/after refactoring
- [ ] 5.4 Benchmark performance (refactoring should not degrade)

## 6. Code Quality Validation

- [ ] 6.1 Run `uv run pytest --cov=packages/tasky-storage --cov-fail-under=80`
- [ ] 6.2 Verify storage coverage maintains or improves
- [ ] 6.3 Run `uv run ruff check --fix`
- [ ] 6.4 Run `uv run pyright`
- [ ] 6.5 Verify duplicate code is eliminated (grep for `_snapshot_to_task` returns only definition)
