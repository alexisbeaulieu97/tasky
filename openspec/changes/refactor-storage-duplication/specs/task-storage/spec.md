## ADDED Requirements

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

6. **Error Types**: Define consistent exceptions inheriting from `StorageError`
   - `SnapshotConversionError`: Invalid snapshot data
   - `StorageDataError`: Invalid task field values or Pydantic validation failure
   - `TransactionConflictError`: Concurrent write conflicts
   - All must have clear, actionable error messages and context

**Test Requirements**:
- Serialization roundtrip (task → `.model_dump_json()` → `.model_validate_json()`) must produce identical objects
- Error classes must preserve context information for debugging
- Both JSON and SQLite backends must use same utilities and produce identical output

#### Scenario: Snapshot conversion is unified
- **GIVEN** a storage backend needs to convert a snapshot to TaskModel
- **WHEN** the backend calls `convert_snapshot_to_task(snapshot)`
- **THEN** conversion uses the same logic regardless of backend type
- **AND** error handling is consistent across all backends (SnapshotConversionError with message)
- **AND** all task fields are properly deserialized
- **AND** datetime fields are parsed from ISO 8601 strings

#### Scenario: Serialization is standardized
- **GIVEN** different backends need to serialize TaskModel objects
- **WHEN** backends call `serialize_task_to_json(task)`
- **THEN** datetime and enum values are serialized identically
- **AND** output format is consistent across JSON and SQLite backends (ISO 8601 datetimes, string enums)
- **AND** serialized data is re-parseable via `deserialize_task_from_json()` into identical TaskModel
- **AND** key ordering is deterministic (e.g., alphabetical)

### Requirement: Backend Implementation Consistency

All storage backends SHALL implement core operations identically, with differences only in storage mechanism.

#### Scenario: Error handling is identical
- **GIVEN** a snapshot conversion error occurs in shared utility
- **WHEN** the error is raised (e.g., SnapshotConversionError, TaskValidationError, TransactionConflictError, IOError, FileNotFoundError)
- **THEN** all backends handle the error identically:
  - **SnapshotConversionError**: Invalid snapshot dict → logged as error → user sees "Task data corrupted" message
  - **TaskValidationError**: Invalid task data (bad UUID, invalid enum) → logged as validation_error → returns 400 Bad Request
  - **TransactionConflictError**: Concurrent write conflict → logged as conflict → retries once or fails cleanly
  - **IOError/FileNotFoundError**: Disk I/O failure (JSON file not found, SQLite locked) → logged as error → returns 500 Internal Error
- **AND** error messages are consistent across backends (same wording, context, suggestions)
- **AND** error recovery is identical (no retry for validation, retry once for transient I/O)
- **AND** all backends return consistent status codes/exceptions to callers

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
