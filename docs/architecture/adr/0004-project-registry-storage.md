# ADR-004: Project Registry Storage Format

## Status
Accepted

## Context
The global project registry needs to track all tasky projects across the filesystem to enable commands like:
- `tasky project list` - Show all registered projects
- `tasky task list --project work` - Operate on a specific project from anywhere
- `tasky project discover ~/code` - Find and register projects recursively

The registry must:
1. Support thousands of projects without performance degradation
2. Be human-readable for debugging
3. Handle concurrent access safely
4. Work on all platforms (macOS, Linux, Windows)
5. Survive crashes without corruption

Storage options considered:
- JSON file
- SQLite database
- TOML file
- Binary format (pickle, msgpack)

## Decision
We use a **JSON file** (`~/.tasky/registry.json`) as the project registry storage format.

**Structure:**
```json
{
  "version": "1.0",
  "projects": [
    {
      "name": "work",
      "path": "/Users/alice/projects/work-tasks",
      "created_at": "2025-01-15T10:30:00Z",
      "last_accessed": "2025-01-15T14:22:00Z",
      "backend_type": "sqlite"
    },
    {
      "name": "personal",
      "path": "/Users/alice/personal/tasks",
      "created_at": "2025-01-10T08:15:00Z",
      "last_accessed": "2025-01-15T09:00:00Z",
      "backend_type": "json"
    }
  ]
}
```

**Implementation Details:**
- **Read-Modify-Write with file locking** to prevent concurrent modification issues
- **Atomic writes** using temp file + rename pattern for crash safety
- **Versioned schema** to support future migrations
- **File size monitoring** with pagination for large registries (1000+ projects)

## Consequences

### Positive
- **Human-readable**: Easy to debug, inspect, and manually edit if needed
- **Cross-platform**: JSON works everywhere, no binary compatibility issues
- **Simple**: No external dependencies (SQLite would require additional setup)
- **Git-friendly**: Can version control (though typically wouldn't)
- **Lightweight**: Fast for typical workloads (<100 projects)
- **Easy backups**: Just copy the file

### Negative
- **Performance at scale**: Linear search for lookups (acceptable up to ~1000 projects)
- **No query optimization**: Can't index by path or name without loading entire file
- **File locking complexity**: Need OS-specific locking for concurrent access
- **Memory overhead**: Must load entire registry into memory for modifications

## Alternatives Considered

### Alternative 1: SQLite Database
Store registry in `~/.tasky/registry.db`:

**Pros:**
- Indexed lookups (O(log n) instead of O(n))
- Built-in concurrency control (ACID transactions)
- Scales to millions of projects
- No file locking complexity

**Rejected because:**
- Over-engineered for typical workloads (most users have <50 projects)
- Harder to debug (binary format, need SQL queries)
- More complexity: schema migrations, database corruption handling
- Not human-readable

**Revisit criteria:** If benchmarks show >1000 projects are common, migrate to SQLite

### Alternative 2: TOML File
Use `~/.tasky/registry.toml` instead of JSON:

**Pros:**
- More human-friendly syntax
- Supports comments
- Same as project config format

**Rejected because:**
- Harder to parse (requires external library)
- More verbose for list-heavy data
- Atomic writes more complex (TOML libraries typically don't support streaming)

### Alternative 3: Binary Format (MessagePack, Pickle)
Use binary serialization:

**Rejected because:**
- Not human-readable (debugging nightmare)
- Platform/version compatibility risks
- No significant performance benefit for this use case

### Alternative 4: Directory of Individual Files
Store each project as `~/.tasky/projects/work.json`:

**Rejected because:**
- Harder to implement pagination/listing
- More file system overhead
- Race conditions on directory listings
- No atomic "add multiple projects" operation

## Performance Characteristics

**Tested with 500 projects:**
- `list_projects()`: ~2ms (load + deserialize entire file)
- `get_project(name)`: ~2ms (linear search after load)
- `register_project()`: ~5ms (load + modify + atomic write)

**Mitigation for large registries:**
- Pagination support: `list_projects(limit=50, offset=100)`
- LRU cache for recent lookups (future enhancement)
- Migrate to SQLite if 1000+ projects becomes common

## References
- `packages/tasky-projects/src/tasky_projects/registry.py` - Registry implementation
- `packages/tasky-projects/src/tasky_projects/models.py` - ProjectRegistry model
- File locking: https://docs.python.org/3/library/fcntl.html (Unix) / msvcrt (Windows)
