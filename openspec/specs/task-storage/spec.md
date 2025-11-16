# task-storage Specification

## Purpose
This specification defines the requirements and guarantees for task storage backends in the tasky project. It ensures data integrity, error resilience, and safe concurrency across JSON and SQLite implementations. The spec addresses critical scenarios including database corruption recovery, backend migration with data preservation, and concurrent access patterns. Target audience includes backend implementers and services consuming storage APIs.
## Requirements
### Requirement: Storage Backend Error Resilience

Storage backends SHALL handle error conditions gracefully and provide clear error messages. Backends MUST validate data integrity on read, handle database errors, and recover from transient failures. Error paths SHALL be tested comprehensively.

#### Scenario: Database becomes locked during operation
- **WHEN** another process holds a lock on the SQLite database
- **THEN** the backend SHALL wait with exponential backoff (configurable timeout)
- **AND** if timeout expires, raise `StorageError` with message: "Database is locked; another process may be using it"
- **AND** operation SHALL not corrupt database state

#### Scenario: Corrupted task data in database
- **WHEN** a task snapshot in storage is malformed or incomplete
- **THEN** `find_tasks()` SHALL report which task is corrupted
- **AND** operation SHALL continue with other tasks (fail partial, not total)
- **AND** user is informed via error message which task to review

#### Scenario: Concurrent modifications during transaction
- **WHEN** another process modifies a task while transaction is in progress
- **THEN** backend SHALL detect serialization conflict
- **AND** operation SHALL fail with clear error (not silent data loss)
- **AND** caller can retry safely

### Requirement: Backend Migration Integrity

When switching from one backend to another, all task data, timestamps, and metadata SHALL be preserved exactly. The system SHALL provide rollback capability and validation.

#### Scenario: Successful JSON to SQLite migration
- **WHEN** user initiates migration from JSON to SQLite backend
- **THEN** all tasks are copied with identical field values
- **AND** all timestamps (created_at, updated_at, due_date) are preserved
- **AND** task IDs remain unchanged
- **AND** no tasks are lost or duplicated

#### Scenario: Large-scale migration (1000+ tasks)
- **WHEN** migrating a project with 1000+ tasks
- **THEN** migration completes without memory exhaustion
- **AND** all tasks are verified after migration (checksum validation)
- **AND** performance is acceptable (<5 seconds for 10k tasks)

#### Scenario: Migration fails and rolls back
- **WHEN** migration encounters an error (disk full, permission denied)
- **THEN** original backend remains unchanged
- **AND** new backend is left in a recoverable state
- **AND** user is informed which backend is currently active

### Requirement: Concurrency & Data Durability

Storage backends SHALL safely handle concurrent access and provide data durability guarantees under load.

#### Scenario: Multiple concurrent writers
- **WHEN** 10+ threads write tasks simultaneously to SQLite
- **THEN** no data corruption occurs
- **AND** all writes complete successfully
- **AND** final task count equals number of writes

#### Scenario: Long-running transaction under load
- **WHEN** a transaction takes >1 second while other writes occur
- **THEN** isolation is maintained (no dirty reads)
- **AND** transaction eventually completes (not deadlocked)
- **AND** other operations are not blocked indefinitely

### Requirement: Registry Corruption Recovery

The project registry SHALL detect and recover from file corruption automatically.

#### Scenario: Corrupted registry file
- **WHEN** registry.json is partially written or corrupted
- **THEN** system detects corruption on load
- **AND** falls back to backup file if available
- **AND** user sees informational message about recovery
- **AND** service continues operation

#### Scenario: Backup file available but main file corrupt
- **WHEN** registry.json is corrupt and registry.json.bak exists
- **THEN** backup is restored as new main file
- **AND** new backup is created from main
- **AND** no projects are lost

### Requirement: Shared Storage Utilities

The tasky-storage package SHALL provide shared utility functions for common operations needed by all backends, eliminating code duplication and ensuring consistency.

#### Scope: Shared Responsibilities

The `tasky_storage.utils` module SHALL provide:
- **Snapshot Conversion**: Convert raw snapshots (dict, database rows) to TaskModel instances
- **Serialization**: Serialize TaskModel to JSON-compatible format (datetime ISO 8601, enums as strings)
- **Deserialization**: Parse JSON back to TaskModel with validation
- **Query/Filter Builders**: Construct consistent filter predicates across backends
- **Pagination**: Apply limit/offset consistently
- **Transaction Helpers**: Atomic write wrappers for multi-operation batches
- **Caching Hooks**: Registry for storage layer caching (if needed by higher-level code)
- **Connection/Retention Config**: Shared timeout, retry, and cleanup settings
- **Validation Helpers**: Validate task data before persistence (UUID format, enum values, etc.)
- **Error Types**: Consistent exception hierarchy (SnapshotConversionError, IOError, TransactionConflictError, ValidationError)
- **Migration Helpers**: Utilities for schema evolution (versioning, field renames, etc.)

#### API/Interface Contract

**Module Location**: `packages/tasky-storage/tasky_storage/utils.py`

The utilities module SHALL provide consolidated functions/helpers (implementers choose the API shape) for:

1. **Snapshot Conversion**: Convert raw snapshots (dicts, database rows) to TaskModel instances
   - Must raise clear errors when snapshot is invalid (inherit from `StorageError`)
   - Must deserialize datetime fields from ISO 8601 format
   - MUST consolidate logic from existing mappers in `tasky_storage.backends.{json,sqlite}.mappers`

2. **Serialization**: Serialize TaskModel to JSON-compatible format (use Pydantic `.model_dump(mode="json")`)
   - All datetime fields → ISO 8601 strings with timezone (e.g., "2025-11-15T14:30:45Z")
   - All enum fields → string values (e.g., status="pending")
   - Null values → JSON null (preserved, not omitted)
   - Nested structures (subtasks, blockers) → nested in JSON

3. **Deserialization**: Parse JSON back to TaskModel via Pydantic `.model_validate()`
   - Pydantic validates required fields and types automatically
   - Raise `StorageDataError` with context if Pydantic validation fails

4. **Filtering**: Build backend-agnostic filter predicates
   - Support filtering by status, search text, date ranges
   - Each backend converts predicates to its native query format

5. **Pagination**: Apply limit/offset to results
   - Must handle edge cases (limit=0, offset > total, etc.)

6. **Error Types**: Define a custom exception hierarchy to replace raw built-in exceptions
   - All storage operations SHALL raise only custom exceptions inheriting from `StorageError` (base class)
   - No backend SHALL raise built-in exceptions (`IOError`, `FileNotFoundError`, `ValueError`, etc.) directly
   - Each custom error accepts an optional `cause` parameter to wrap the original exception for debugging
   - Error messages are actionable and consistent across all backends

   **Exception Hierarchy**:
   ```
   StorageError (base)
     ├── SnapshotConversionError (invalid snapshot dict → TaskModel conversion)
     ├── StorageDataError (Pydantic validation, field validation, or data type failures)
     │   └── [Optional] TaskValidationError (alias; inherits from StorageDataError for naming clarity)
     ├── TransactionConflictError (concurrent write conflicts detected)
     └── StorageIOError (wraps OS/I/O errors: OSError, FileNotFoundError, etc.)
   ```

   **Error Behavior Mapping**:
   - `SnapshotConversionError` → Log level: `ERROR` → User message: "Task data corrupted" → Action: Do not retry
   - `StorageDataError` / `TaskValidationError` → Log level: `WARNING` (validation_error) → HTTP: 400 Bad Request → Action: Do not retry
   - `TransactionConflictError` → Log level: `WARNING` (conflict) → Action: Retry once, then fail cleanly
   - `StorageIOError` → Log level: `ERROR` → HTTP: 500 Internal Server Error → Action: Retry once for transient I/O, fail cleanly if persistent

**Test Requirements**:
- Serialization roundtrip (task → `.model_dump_json()` → `.model_validate_json()`) must produce identical objects
- Error classes must preserve context information (original exception in `cause`) for debugging
- Both JSON and SQLite backends must use same utilities and produce identical output
- All backends wrap platform-specific exceptions (OSError, sqlite3.OperationalError, etc.) in custom error classes

#### Scenario: Snapshot conversion is unified
- **GIVEN** a storage backend needs to convert a snapshot to TaskModel
- **WHEN** the backend calls `convert_snapshot_to_task(snapshot)` with invalid data (missing required field)
- **THEN** the utility raises `SnapshotConversionError` (never `ValueError` or `KeyError`)
- **AND** error message is actionable: "Failed to convert snapshot: missing required field 'id'"
- **AND** the original exception is preserved in the `cause` parameter
- **AND** all task fields are properly deserialized when snapshot is valid
- **AND** datetime fields are parsed from ISO 8601 strings

#### Scenario: Serialization is standardized
- **GIVEN** different backends need to serialize TaskModel objects
- **WHEN** backends call `serialize_task_to_json(task)`
- **THEN** datetime and enum values are serialized identically
- **AND** output format is consistent across JSON and SQLite backends (ISO 8601 datetimes, string enums)
- **AND** serialized data is re-parseable via `deserialize_task_from_json()` into identical TaskModel
- **AND** key ordering is deterministic (e.g., alphabetical)

### Requirement: Backend Implementation Consistency

All storage backends SHALL implement core operations identically, with differences only in storage mechanism. All backends SHALL use the custom error hierarchy defined in the Shared Storage Utilities requirement.

#### Scenario: Error handling is identical and uses custom exceptions
- **GIVEN** an operation fails in either JSON or SQLite backend
- **WHEN** the backend encounters one of these conditions:
  1. Invalid snapshot dict (missing fields, bad types) → raises `SnapshotConversionError`
  2. Pydantic validation fails (invalid UUID, enum value) → raises `StorageDataError` or `TaskValidationError`
  3. Concurrent write detected (file timestamp mismatch, SQLite BUSY) → raises `TransactionConflictError`
  4. Disk I/O failure (file not found, locked, permission denied) → raises `StorageIOError`
- **THEN** all backends handle the error identically:
  - Log level matches (ERROR for corruption/I/O, WARNING for validation/conflict)
  - User-facing message is identical across backends
  - Retry logic follows the mapping (no retry for validation, 1 retry for transient I/O)
  - HTTP/exception bubbled to caller matches the error type
- **AND** original exception is wrapped in `cause` for debugging
- **AND** error messages are consistent in wording and context
- **AND** no backend raises raw built-in exceptions (IOError, FileNotFoundError, ValueError, etc.)

#### Scenario: Backends are functionally equivalent across all operations
- **GIVEN** a sequence of test operations: Create, Read, Update, Delete, Filter by status, Filter by search, Pagination, Multi-operation transaction
- **WHEN** the same sequence runs against both JSON and SQLite backends:

**Operations to Test**:
1. **Create**: Add 5 tasks with various priorities and dates
2. **Read**: Fetch each task by ID (verify all fields match initial values)
3. **Update**: Change name, details, priority, due_date on task #1
4. **Filter by Status**: List all "pending" tasks (expect 4, excluding any completed)
5. **Filter by Search**: Find tasks with "urgent" in name/details
6. **Filter by Date Range**: Find tasks created between date1 and date2
7. **Pagination**: List tasks with limit=2, offset=1
8. **Delete**: Remove one task, verify it's gone from all queries
9. **Transaction**: Update 3 tasks atomically (all succeed or all rollback)

**Expected Outcomes** (identical across JSON and SQLite):
- Final task count matches: 4 remaining (5 created - 1 deleted)
- Each task has identical field values (name, details, priority, dates, status)
- Timestamps match (created_at, updated_at to millisecond precision)
- Filter results are identical (same task IDs, same order)
- Pagination returns same tasks in same order
- Transaction either fully commits or fully rolls back (no partial state)

**Example Concrete Inputs & Expected State**:
```
Initial: Create 5 tasks
  T1: name="Fix login", priority="high", status="pending", created_at=2025-11-15T10:00:00Z
  T2: name="Write docs", priority="low", status="pending", created_at=2025-11-15T11:00:00Z
  T3: name="Review PR", priority="normal", status="completed", created_at=2025-11-15T12:00:00Z
  T4: name="Deploy to prod", priority="high", status="pending", created_at=2025-11-15T13:00:00Z
  T5: name="Fix urgent bug", priority="high", status="pending", created_at=2025-11-15T14:00:00Z

Operations:
  1. Read T1 → verify all fields match
  2. Update T1: name="Fix login bug" → verify updated_at changes, name matches
  3. Filter status="pending" → expect [T1, T2, T4, T5] (T3 is completed)
  4. Filter search="Fix" → expect [T1, T5] (both have "Fix" in name)
  5. Filter created_after=2025-11-15T12:30:00Z → expect [T4, T5]
  6. Pagination(limit=2, offset=1) → expect 2nd and 3rd tasks from filtered result
  7. Delete T3 → verify count = 4, T3 not in any filter result
  8. Transaction: Update T1 priority="urgent", T2 priority="urgent", T4 status="completed"
     → Verify all 3 updated or all 3 unchanged (not partial)

Final Verification:
  - Total tasks: 4 ✓
  - T1 name="Fix login bug", priority="urgent" ✓
  - T2 priority="urgent" ✓
  - T4 status="completed" ✓
  - All timestamps preserved (created_at unchanged, updated_at reflects operations) ✓
  - JSON backend state identical to SQLite backend state ✓
```

