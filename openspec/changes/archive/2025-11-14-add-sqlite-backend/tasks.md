# Implementation Tasks: Add SQLite Backend

This document outlines the ordered implementation tasks for the SQLite backend. Tasks are designed to build the feature incrementally with validation at each step.

## Task Checklist

### Phase 1: Storage Adapter Foundation (SQLite Backend Module)

- [x] **Task 1.1**: Create SQLite backend module structure
  - Create `packages/tasky-storage/src/tasky_storage/backends/sqlite/` directory
  - Create `__init__.py`, `repository.py`, `storage.py`, `models.py` files
  - Set up imports and module exports
  - **Validation**: Module imports without errors

- [x] **Task 1.2**: Implement database schema creation
  - Create `packages/tasky-storage/src/tasky_storage/backends/sqlite/schema.py`
  - Define SQL CREATE TABLE statement for tasks table
  - Define SQL CREATE INDEX statements (status, project_id, created_at, composite)
  - Implement schema validation (PRAGMA integrity_check)
  - **Validation**: Schema creation tested in isolation

- [x] **Task 1.3**: Implement connection management and pooling
  - Create connection manager with RLock per database file
  - Implement WAL mode pragmas (journal_mode, synchronous, busy_timeout, foreign_keys)
  - Implement connection lifecycle (acquire, release, cleanup)
  - Add connection pool with lazy initialization
  - **Validation**: Connections created and closed properly; thread safety verified

- [x] **Task 1.4**: Implement task serialization mappers
  - Create `packages/tasky-storage/src/tasky_storage/backends/sqlite/mappers.py`
  - Implement `task_model_to_snapshot()` (reuse from JSON if possible)
  - Implement `snapshot_to_task_model()` (reuse from JSON if possible)
  - Implement `row_to_snapshot()` for converting sqlite3.Row to dict
  - **Validation**: Round-trip conversion preserves all task data

### Phase 2: SQLite Repository Implementation

- [x] **Task 2.1**: Implement `SqliteTaskRepository` class
  - Create `packages/tasky-storage/src/tasky_storage/backends/sqlite/repository.py`
  - Implement class with connection management
  - Add type hints and docstrings
  - Set up error handling with domain exceptions
  - **Validation**: Class structure matches TaskRepository protocol

- [x] **Task 2.2**: Implement repository initialization
  - Implement `initialize()` method
  - Create schema if not exists
  - Verify database integrity
  - Handle already-initialized database gracefully
  - **Validation**: Manual test: `repo.initialize()` creates tables

- [x] **Task 2.3**: Implement CRUD operations
  - Implement `save_task(task: TaskModel) -> None` with INSERT OR REPLACE
  - Implement `get_task(task_id: UUID) -> TaskModel | None`
  - Implement `get_all_tasks() -> list[TaskModel]`
  - Implement `delete_task(task_id: UUID) -> bool`
  - Implement `task_exists(task_id: UUID) -> bool`
  - All operations use transaction context managers
  - **Validation**: Manual testing with small task set

- [x] **Task 2.4**: Implement filtering by status
  - Implement `get_tasks_by_status(status: TaskStatus) -> list[TaskModel]`
  - Use indexed status column for efficiency
  - Return empty list when no matches
  - **Validation**: Filter returns correct subset; verify query uses index

- [x] **Task 2.5**: Implement error handling and recovery
  - Map sqlite3 exceptions to domain exceptions
  - Handle database locked (busy_timeout should cover)
  - Handle integrity constraint violations
  - Handle corrupted database on initialize
  - **Validation**: Tests verify correct exception types raised

### Phase 3: Backend Registration and Wiring

- [x] **Task 3.1**: Create SQLite backend factory function
  - Implement `sqlite_factory(path: Path) -> SqliteTaskRepository`
  - Ensure factory signature matches `BackendFactory` protocol
  - Add docstring and type hints
  - **Validation**: Factory creates repository; type checker passes

- [x] **Task 3.2**: Implement self-registration
  - Add registration call in `packages/tasky-storage/src/tasky_storage/backends/sqlite/__init__.py`
  - Import global registry and call `registry.register("sqlite", sqlite_factory)`
  - Ensure registration happens on module import
  - Make idempotent (safe to import multiple times)
  - **Validation**: Import tasky_storage; verify "sqlite" available via registry

- [x] **Task 3.3**: Update storage module exports
  - Update `packages/tasky-storage/src/tasky_storage/__init__.py`
  - Export SqliteTaskRepository and factory
  - Ensure backward compatibility (JSON still exported)
  - **Validation**: `from tasky_storage import SqliteTaskRepository` works

- [x] **Task 3.4**: Update settings for SQLite configuration
  - Update `packages/tasky-settings/src/tasky_settings/factory.py`
  - Add SQLite URI parsing: `sqlite://<path>`
  - Route sqlite:// URIs to SQLite backend factory
  - **Validation**: `create_task_service()` with `sqlite://db.db` returns SQLite repo

### Phase 4: Unit & Integration Testing

- [x] **Task 4.1**: Create SQLite backend unit tests
  - Create `packages/tasky-storage/tests/test_sqlite_repository.py`
  - Test CRUD operations (create, read, update, delete)
  - Test filtering by status
  - Test empty repository behavior
  - Test schema creation
  - Test transactions (insert fails on duplicate)
  - **Validation**: Run `uv run pytest packages/tasky-storage/tests/test_sqlite_repository.py -v`

- [x] **Task 4.2**: Test concurrent access
  - Add concurrent read/write tests
  - Test multiple threads creating different tasks
  - Test thread A writing while thread B reads
  - Test two threads writing same task ID (second should succeed with update or fail)
  - **Validation**: Concurrent tests pass; no deadlocks or data corruption

- [x] **Task 4.3**: Test error handling and recovery
  - Test database locked scenario (trigger with low timeout)
  - Test corrupted database detection
  - Test constraint violation handling
  - Test missing file handling
  - **Validation**: Correct exceptions raised; helpful messages

- [x] **Task 4.4**: Test serialization and round-trip
  - Create task in memory → save to SQLite → retrieve → verify equality
  - Test with all TaskStatus values
  - Test with null/optional fields
  - Test with special characters in name/description
  - **Validation**: Data integrity verified

- [x] **Task 4.5**: Test initialization and idempotence
  - Test `initialize()` creates schema first time
  - Test second `initialize()` call succeeds without error
  - Test schema matches expected structure
  - Test indexes exist and are correct
  - **Validation**: Schema correct; initialization idempotent

### Phase 5: Integration with Filtering Feature

- [x] **Task 5.1**: Verify task filtering works with SQLite
  - Run existing filtering tests against SQLite backend
  - Create tasks with mixed statuses
  - Test `--status pending` filtering via CLI
  - Test `--status completed` filtering via CLI
  - Verify results match JSON backend behavior
  - **Validation**: `uv run pytest packages/tasky-cli/tests/ -k filtering -v` passes with SQLite

- [x] **Task 5.2**: Test filtering performance
  - Create 1000+ tasks with mixed statuses
  - Query by status and verify O(log n) performance (index-based)
  - Compare with JSON backend if applicable
  - **Validation**: Query completes in <100ms for 10k tasks

### Phase 6: End-to-End & CLI Integration

- [x] **Task 6.1**: Test project initialization with SQLite
  - Initialize project with `--storage sqlite://.tasky/tasks.db`
  - Verify database file created
  - Verify schema matches expected
  - Verify subsequent commands work
  - **Validation**: Manual test: `uv run tasky project init --storage sqlite://test.db`

- [x] **Task 6.2**: Test full CLI workflows with SQLite
  - Create project with SQLite backend
  - Create multiple tasks with different statuses
  - List all tasks
  - Filter tasks by status
  - Update task status
  - Delete task
  - **Validation**: All workflows work identically to JSON backend

- [x] **Task 6.3**: Test cross-backend compatibility
  - Initialize project with JSON backend
  - Verify JSON and SQLite backends coexist (both registered)
  - Create project with SQLite backend
  - Verify no conflicts
  - **Validation**: Both backends available; no registry conflicts

- [x] **Task 6.4**: Create end-to-end test scenarios
  - Create `tests/test_sqlite_cli_workflow.py` (if needed)
  - Test: init → create → filter → update → delete workflow
  - Test: concurrent task creation via CLI
  - **Validation**: End-to-end tests pass

### Phase 7: Testing & Quality Assurance

- [x] **Task 7.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify no tests broken by SQLite addition
  - Check test coverage for SQLite backend (target ≥80%)
  - **Validation**: All tests pass (baseline + new SQLite tests)

- [x] **Task 7.2**: Code quality and linting
  - Run `uv run ruff check --fix` on new SQLite modules
  - Run `uv run ruff format` on new SQLite modules
  - Fix any import ordering issues
  - Verify type hints are complete
  - **Validation**: No linting errors; clean ruff output

- [x] **Task 7.3**: Manual regression testing
  - Initialize fresh project with JSON backend
  - Verify all existing features work
  - Initialize fresh project with SQLite backend
  - Verify all existing features work
  - Verify filtering by status works with both backends
  - **Validation**: No regressions; identical behavior

- [x] **Task 7.4**: Documentation updates
  - Add SQLite backend section to README (if exists)
  - Document configuration options (sqlite:// URI format)
  - Document schema and indexes
  - Document migration path from JSON to SQLite (if applicable)
  - **Validation**: Documentation clear and accurate

### Phase 8: Final Validation

- [x] **Task 8.1**: Verify backend registry integration
  - Import tasky_storage
  - Call `registry.list_backends()` and verify ["json", "sqlite"]
  - Call `registry.get("sqlite")` and verify factory returned
  - Create repository via factory and verify it works
  - **Validation**: Registry integration complete

- [x] **Task 8.2**: Verify self-registration idempotency
  - Import tasky_storage multiple times
  - Verify no errors
  - Verify "sqlite" still available
  - **Validation**: Self-registration is idempotent

- [x] **Task 8.3**: Performance validation
  - Create 10,000 tasks in SQLite database
  - Verify filtering by status completes in <1 second
  - Verify retrieval of all tasks completes in <2 seconds
  - Verify schema with indexes performs better than full table scan
  - **Validation**: Performance meets expectations

- [x] **Task 8.4**: Smoke test complete workflow
  - `uv run tasky project init --storage sqlite://.tasky/tasks.db`
  - `uv run tasky task create "Test task 1"`
  - `uv run tasky task create "Test task 2"`
  - `uv run tasky task update 1 --status completed`
  - `uv run tasky task list --status pending`
  - `uv run tasky task list`
  - Verify output matches expectations
  - **Validation**: Complete workflow runs without errors

## Notes

- **Dependencies**: Tasks within phases should follow order; phases can overlap once dependencies met
- **Parallelization**: Phases 1-2 should complete before phases 3+; Phase 4 can start during phase 2
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Rollback**: Each task independently reversible via git; feature can be abandoned at any phase
- **Review Points**:
  - After Phase 2: Repository implementation review
  - After Phase 4: Test coverage review
  - After Phase 6: CLI integration review
  - After Phase 8: Final validation before archiving

## Estimated Duration

- Phase 1: 1 hour (schema + connection management)
- Phase 2: 1.5 hours (repository CRUD + filtering)
- Phase 3: 45 minutes (registration + wiring)
- Phase 4: 1.5 hours (unit + integration tests)
- Phase 5: 30 minutes (filtering integration)
- Phase 6: 45 minutes (CLI + end-to-end tests)
- Phase 7: 45 minutes (quality assurance)
- Phase 8: 30 minutes (final validation)

**Total**: ~7 hours

## Success Criteria

1. All tasks marked `[x]` (complete)
2. All tests pass: `uv run pytest` (baseline + SQLite)
3. Code quality: `uv run ruff check` passes
4. Manual smoke test: `tasky project init --storage sqlite://test.db` and full workflow
5. Performance acceptable: filtering 10k tasks in <1 second
6. Documentation updated
