## 1. SQLite Repository Error Path Testing

- [ ] 1.1 Add tests for `_execute_query()` failure scenarios (database locked, disk full, permission denied)
- [ ] 1.2 Add tests for `find_tasks()` with corrupted task snapshots in database
- [ ] 1.3 Add tests for `save_task()` with foreign key constraint violations
- [ ] 1.4 Add tests for `delete_task()` with integrity constraint violations
- [ ] 1.5 Add tests for concurrent modifications during transaction (serialization errors)
- [ ] 1.6 Verify error messages are user-friendly and actionable
- [ ] 1.7 Run `uv run pytest packages/tasky-storage/tests/test_sqlite_repository.py --cov` to verify ≥80%

## 2. Concurrency & Stress Testing

- [ ] 2.1 Add thread-pool stress test: 10 concurrent writers to SQLite
- [ ] 2.2 Add test for WAL mode checkpoint behavior under load
- [ ] 2.3 Add test for connection pool exhaustion (verify recovery)
- [ ] 2.4 Add test for concurrent reads + writes (verify no data corruption)
- [ ] 2.5 Add test for long-running transactions (verify timeout handling)
- [ ] 2.6 Benchmark performance under concurrent load (document baseline)

## 3. Backend Migration Integration Tests

- [ ] 3.1 Create test: JSON → SQLite migration preserves all task fields
- [ ] 3.2 Create test: SQLite → JSON migration preserves all task fields
- [ ] 3.3 Create test: Backend switching with 1000+ tasks (stress test)
- [ ] 3.4 Create test: Migration fails gracefully (rollback on error)
- [ ] 3.5 Create test: Task filters work identically after migration
- [ ] 3.6 Create test: Timestamps are preserved across migration
- [ ] 3.7 Run `uv run pytest tests/ -k migration` to verify all pass

## 4. Registry Corruption Recovery Testing

- [ ] 4.1 Add test: Registry file corruption triggers backup + recovery
- [ ] 4.2 Add test: Partially-written registry file is handled gracefully
- [ ] 4.3 Add test: Backup file is used when main registry is corrupt
- [ ] 4.4 Add test: Recovery creates valid registry state
- [ ] 4.5 Verify logging indicates recovery action taken

## 5. Cross-Backend Behavioral Tests

- [ ] 5.1 Add parameterized tests for all storage operations with both backends
- [ ] 5.2 Create test comparing filtering results between JSON and SQLite (100+ tasks)
- [ ] 5.3 Create test comparing sort order consistency across backends
- [ ] 5.4 Create test for edge cases: empty database, single task, max-length strings
- [ ] 5.5 Run full test suite against both backends: `uv run pytest --backends json,sqlite`

## 6. Validation & Coverage

- [ ] 6.1 Run `uv run pytest --cov=packages --cov-fail-under=80` (verify no regressions)
- [ ] 6.2 Generate coverage report: `uv run pytest --cov=packages/tasky-storage --cov-report=html`
- [ ] 6.3 Verify SQLite coverage ≥80% (currently 54%)
- [ ] 6.4 Run `uv run ruff check --fix`
- [ ] 6.5 Run `uv run pyright`
