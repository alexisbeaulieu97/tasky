## 1. SQLite Repository Error Path Testing

- [x] 1.1 Add tests for `_execute_query()` failure scenarios (database locked, disk full, permission denied)
- [x] 1.2 Add tests for `find_tasks()` with corrupted task snapshots in database
- [x] 1.3 Add tests for `save_task()` with foreign key constraint violations
- [x] 1.4 Add tests for `delete_task()` with integrity constraint violations
- [x] 1.5 Add tests for concurrent modifications during transaction (serialization errors)
- [x] 1.6 Verify error messages are user-friendly and actionable
- [x] 1.7 Run `uv run pytest packages/tasky-storage/tests/test_sqlite_repository.py --cov` to verify ≥80%

## 2. Concurrency & Stress Testing

- [x] 2.1 Add thread-pool stress test: 10 concurrent writers to SQLite
- [x] 2.2 Add test for WAL mode checkpoint behavior under load
- [x] 2.3 Add test for connection pool exhaustion (verify recovery)
- [x] 2.4 Add test for concurrent reads + writes (verify no data corruption)
- [x] 2.5 Add test for long-running transactions (verify timeout handling)
- [x] 2.6 Benchmark performance under concurrent load (document baseline)

## 3. Backend Migration Integration Tests

- [x] 3.1 Create test: JSON → SQLite migration preserves all task fields
- [x] 3.2 Create test: SQLite → JSON migration preserves all task fields
- [x] 3.3 Create test: Backend switching with 1000+ tasks (stress test)
- [x] 3.4 Create test: Migration fails gracefully (rollback on error)
- [x] 3.5 Create test: Task filters work identically after migration
- [x] 3.6 Create test: Timestamps are preserved across migration
- [x] 3.7 Run `uv run pytest tests/ -k migration` to verify all pass

## 4. Registry Corruption Recovery Testing

- [x] 4.1 Add test: Registry file corruption triggers backup + recovery
- [x] 4.2 Add test: Partially-written registry file is handled gracefully
- [x] 4.3 Add test: Backup file is used when main registry is corrupt
- [x] 4.4 Add test: Recovery creates valid registry state
- [x] 4.5 Verify logging indicates recovery action taken

## 5. Cross-Backend Behavioral Tests

- [x] 5.1 Add parameterized tests for all storage operations with both backends
- [x] 5.2 Create test comparing filtering results between JSON and SQLite (100+ tasks)
- [x] 5.3 Create test comparing sort order consistency across backends
- [x] 5.4 Create test for edge cases: empty database, single task, max-length strings
- [x] 5.5 Run full test suite against both backends: `uv run pytest --backends json,sqlite`

## 6. Validation & Coverage

- [x] 6.1 Run `uv run pytest --cov=packages --cov-fail-under=80` (verify no regressions)
- [x] 6.2 Generate coverage report: `uv run pytest --cov=packages/tasky-storage --cov-report=html`
- [x] 6.3 Verify SQLite coverage ≥80% (currently 54%)
- [x] 6.4 Run `uv run ruff check --fix`
- [x] 6.5 Run `uv run pyright`

