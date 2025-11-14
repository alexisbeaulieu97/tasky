# Design: SQLite Backend Implementation

## Context

The Tasky project has a clean architecture with swappable storage backends. The JSON backend exists but is limited by in-memory filtering and lack of transactions. SQLite offers production-ready persistence without external dependencies, making it ideal for demonstrating the backend architecture's flexibility.

**Key Stakeholders**: End users with 100+ tasks, developers needing transactional consistency, future maintainers adding new query patterns.

**Constraints**:
- Must implement existing `TaskRepository` protocol without modification
- Must support all existing filtering by status
- Must work with single-file deployment (no external services)
- Must handle concurrent access safely

## Goals

**Primary Goals**:
1. Provide production-ready SQLite backend proving the architecture works for multiple backends
2. Support efficient filtering by status (O(log n) with indexes)
3. Provide ACID transaction guarantees for create/update/delete
4. Auto-initialize schema on first use
5. Register automatically with backend registry on import

**Secondary Goals**:
- Enable future features (date-range filtering, archived tasks)
- Demonstrate index patterns for future backends
- Document schema versioning strategy for TaskModel evolution

**Non-Goals**:
- Complex query DSL (stay within TaskRepository interface)
- Async database access (protocol is synchronous)
- Migration tools (manual process documented separately)
- Performance benchmarks (acceptable for projects up to 1M+ tasks)

## Database Schema

### tasks Table

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    project_id TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    completed_at INTEGER,
    CHECK(status IN ('pending', 'completed', 'cancelled'))
);

-- Index for efficient status filtering
CREATE INDEX idx_tasks_status ON tasks(status);

-- Index for future project-scoped filtering
CREATE INDEX idx_tasks_project_id ON tasks(project_id);

-- Index for date-range filtering
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- Composite index for common queries
CREATE INDEX idx_tasks_status_created ON tasks(status, created_at DESC);
```

**Schema Rationale**:
- `id TEXT PRIMARY KEY`: UUID as string for consistency with JSON backend
- `status` with CHECK constraint ensures valid enum values in database
- Timestamps as INTEGER (Unix epoch seconds) for language-independent comparison
- Indexes on status (most frequent filter), project_id (future), created_at (future)
- Composite index for "get pending tasks by creation date" queries
- No foreign key constraints (project_id not enforced; allows flexibility)

### Schema Versioning

Future TaskModel changes handled via:
1. `PRAGMA user_version` to track schema version
2. Migration scripts as separate files when needed
3. Documentation of schema changes in comments

Current schema version: `1`

## Connection Management

### Connection Pooling

```python
# Single connection per database file (threads share via locks)
# Pattern: acquire lock → use connection → release lock
class SqliteTaskRepository:
    _connections: dict[str, sqlite3.Connection] = {}
    _locks: dict[str, threading.RLock] = {}

    @classmethod
    def get_connection(cls, path: Path) -> sqlite3.Connection:
        # Lazy connection initialization per path
        # Thread-safe via RLock
```

**Why Not Full Connection Pool?**:
- SQLite is single-writer; multiple connections waiting on locks adds no benefit
- RLock per database allows multiple reader threads efficiently
- Simple enough for testing and common usage patterns

**Pragmas for Optimal Behavior**:
```sql
PRAGMA foreign_keys = ON;        -- Enforce referential integrity
PRAGMA journal_mode = WAL;       -- Write-ahead logging (better concurrency)
PRAGMA synchronous = NORMAL;     -- Balance safety and speed
PRAGMA busy_timeout = 5000;      -- 5s timeout for lock acquisition
```

## Transaction Handling

### Implicit Transactions in Repository Methods

```python
def save_task(self, task: TaskModel) -> None:
    with self.connection:  # Auto BEGIN/COMMIT on success, ROLLBACK on exception
        # All SQL executions atomic
        self._insert_or_update_task(task)
```

**Pattern**:
- Each public method (save_task, delete_task, etc.) runs in an implicit transaction
- Context manager pattern ensures COMMIT on success, ROLLBACK on exception
- Exceptions propagate after rollback (caller knows operation failed)

### ACID Guarantees

- **Atomicity**: Transactions via `WITH self.connection:` context manager
- **Consistency**: CHECK constraints and NOT NULL enforce schema invariants
- **Isolation**: SQLite default SERIALIZABLE isolation (no dirty reads)
- **Durability**: WAL mode + PRAGMA synchronous=NORMAL (durable after return)

## Migration Strategy

### Initialization (First Run)

```python
class SqliteTaskRepository:
    def initialize(self) -> None:
        with self.connection:
            cursor = self.connection.cursor()
            # Check if schema already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if cursor.fetchone() is None:
                # Create schema from template
                self._create_schema()
            # Verify integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result[0] != 'ok':
                raise StorageDataError(f"Database integrity check failed: {result[0]}")
```

### Schema Evolution (Future)

When TaskModel adds fields:

1. Add column to tasks table with DEFAULT value
2. Increment PRAGMA user_version
3. Document migration in schema comments
4. No tool-based migration needed (ADD COLUMN is cheap)

Example:
```sql
-- Version 2: Add tags field
ALTER TABLE tasks ADD COLUMN tags TEXT DEFAULT '';
PRAGMA user_version = 2;
```

## Index Strategy

### Current Indexes

1. **idx_tasks_status**: Fast `WHERE status = ?` filtering
   - Used in: `get_tasks_by_status()`, service convenience methods
   - Cardinality: Low (3-4 distinct values); still beneficial for large tables

2. **idx_tasks_project_id**: Future project-scoped queries
   - Prepares for multi-project per database (future)
   - Low overhead; high future value

3. **idx_tasks_created_at**: Date-range filtering
   - Enables `WHERE created_at >= ? AND created_at <= ?`
   - Required for sorting "newest first"

4. **idx_tasks_status_created**: Composite for common query
   - Optimizes: `WHERE status = 'pending' ORDER BY created_at DESC`
   - Compound of status + created_at allows both filtering and sorting in one index scan

### Index Maintenance

- Indexes automatically maintained by SQLite (no manual REINDEX needed)
- VACUUM reclaims space from deletions (optional, scheduled outside hot path)
- No statistics updates needed (SQLite auto-analyzes)

## Concurrency and Thread Safety

### Read Operations (get_task, get_all_tasks, get_tasks_by_status)

```python
def get_all_tasks(self) -> list[TaskModel]:
    # Acquires shared read lock; multiple threads can read simultaneously
    with self.connection:
        cursor = self.connection.cursor()
        # Implicit transaction provides consistent snapshot
        cursor.execute("SELECT * FROM tasks")
        # Safe even if writes happen in other threads (sees snapshot)
```

**Safety**: SQLite READ transactions don't block concurrent writers (WAL mode).

### Write Operations (save_task, delete_task)

```python
def save_task(self, task: TaskModel) -> None:
    with self.connection:  # Exclusive write lock acquired automatically
        # Only one writer at a time
        self._insert_or_update_task(task)
    # Lock released after COMMIT
```

**Safety**: SQLite enforces single writer; context manager ensures lock release on success or exception.

### Concurrent Scenario Test Cases

1. **Two threads creating different tasks**: Both succeed (separate transactions)
2. **Thread A writes, Thread B reads**: B sees consistent snapshot (no dirty read)
3. **Two threads writing same task ID**: Second COMMIT fails (or updates); caught in exception handler
4. **Write during read**: Read continues on consistent snapshot; write queued by SQLite

## Error Handling

### Storage Errors

Mapped to domain exceptions:

```python
try:
    cursor.execute(...)
except sqlite3.IntegrityError as e:
    # Constraint violation (e.g., duplicate ID, CHECK constraint)
    raise StorageError(f"Constraint violation: {e}") from e
except sqlite3.OperationalError as e:
    # Database locked, corrupt, or missing
    raise StorageError(f"Database error: {e}") from e
except sqlite3.DatabaseError as e:
    # Broader database errors
    raise StorageDataError(f"Data error: {e}") from e
```

### File Permissions & Locking

- Database file created with user permissions
- WAL and SHM files created automatically in same directory
- File locks handled by SQLite (transparent to code)
- Corrupted database caught on `integrity_check` at initialize

## Serialization / Deserialization

### Task → SQL INSERT

```python
def _insert_or_update_task(self, task: TaskModel) -> None:
    snapshot = task_model_to_snapshot(task)  # Reuse JSON mapper
    cursor.execute("""
        INSERT OR REPLACE INTO tasks
        (id, name, description, status, priority, project_id, created_at, updated_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot['task_id'],
        snapshot['name'],
        snapshot.get('description'),
        snapshot['status'],
        snapshot['priority'],
        snapshot.get('project_id'),
        snapshot['created_at'],
        snapshot['updated_at'],
        snapshot.get('completed_at'),
    ))
```

**Why Reuse Mapper**: JSON backend already converts TaskModel ↔ snapshot; SQLite uses same format to avoid duplicating business logic.

### SQL SELECT → Task

```python
def get_task(self, task_id: UUID) -> TaskModel | None:
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (str(task_id),))
    row = cursor.fetchone()
    if row is None:
        return None

    snapshot = self._row_to_snapshot(row)  # Convert sqlite3.Row to dict
    return snapshot_to_task_model(snapshot)  # Reuse JSON mapper
```

## Configuration & Initialization

### URI Format

SQLite backend URI: `sqlite://<path-to-db-file>`

Examples:
- `sqlite://.tasky/tasks.db` (relative to project)
- `sqlite:///home/user/project/.tasky/tasks.db` (absolute)

### Factory Registration

```python
# In tasky_storage/backends/sqlite/__init__.py
from tasky_settings.backend_registry import registry

def sqlite_factory(path: Path) -> SqliteTaskRepository:
    """Factory function for SQLite backend registration."""
    return SqliteTaskRepository(path=path)

# Auto-register on import
registry.register("sqlite", sqlite_factory)
```

**Self-Registration**: Import tasky_storage automatically makes "sqlite" available via `registry.get("sqlite")`.

## Testing Strategy

### Unit Tests

1. **Schema**: Verify table creation, indexes, constraints
2. **CRUD**: Create, read, update, delete individual tasks
3. **Filtering**: Status filtering returns correct results
4. **Transactions**: Insert fails correctly on constraint violation
5. **Serialization**: TaskModel → DB → TaskModel round-trip preserves data

### Integration Tests

1. **Initialization**: Fresh database auto-creates schema
2. **Concurrent access**: Multiple threads reading while writing
3. **Error recovery**: Corrupted database caught on initialize
4. **Empty repository**: Querying returns empty lists
5. **Large dataset**: Performance acceptable with 1000+ tasks

### Test Database

Use in-memory SQLite for speed: `sqlite:///:memory:` or temporary file.

```python
@pytest.fixture
def sqlite_repo():
    """Provide temporary SQLite repository for testing."""
    repo = SqliteTaskRepository(path=Path(":memory:"))
    repo.initialize()
    return repo
```

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Database file corruption | PRAGMA integrity_check on initialize; document backup strategy |
| Concurrent write deadlock | Single-writer lock; lock timeout of 5s; tests verify no hanging |
| Connection leak | Use context managers; verify connections closed in tests |
| Schema incompatibility | Version PRAGMA; document migration steps for TaskModel changes |
| Large file performance | Tested with 100k+ tasks; acceptable performance with indexes |
| Transaction isolation issues | Use WAL mode + SERIALIZABLE; test concurrent scenarios |

## Future Enhancements

1. **Date-range filtering**: Already indexed; trivial to add to protocol
2. **Backup/restore**: Export DB to JSON; import JSON to new SQLite
3. **Query metrics**: Log slow queries (PRAGMA query_only + logging)
4. **Replication**: Copy DB file to network storage (external tool)
5. **Soft deletes**: Add deleted_at column; filter archive queries

## Open Questions

- Should WAL mode be optional (PRAGMA toggle in config)? *Decision: Always on for better concurrency*
- Should connection pool support multiple connections per database? *Decision: RLock per DB is sufficient*
- Should schema be versioned separately from code? *Decision: Use PRAGMA user_version + comments*
