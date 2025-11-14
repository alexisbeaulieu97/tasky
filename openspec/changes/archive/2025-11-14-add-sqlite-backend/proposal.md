# Proposal: Add SQLite Backend

**Change ID**: `add-sqlite-backend`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal introduces a SQLite storage backend for Tasky, complementing the existing JSON backend. The SQLite backend will provide ACID transactions, efficient indexing, structured querying, and production-ready reliability—demonstrating the architectural strength of the swappable backend system.

## Problem Statement

The JSON backend is suitable for small projects and demonstrates the architecture, but lacks:
- **Transactions**: Creating/updating/deleting multiple related tasks without atomicity guarantees
- **Query Efficiency**: Filtering tasks requires loading and scanning the entire JSON file in memory
- **Concurrent Access**: Multiple processes can corrupt data without locking mechanisms
- **Schema Evolution**: Adding new columns requires manual data migration
- **Production Readiness**: No built-in backup, no transactions, no query optimization

SQLite addresses all these concerns with minimal overhead and no external dependencies.

## Why

**Architectural Validation**: Implementing a second production-ready backend validates the registry and self-registration patterns established in the backend-registry and backend-self-registration specs. A single implementation (JSON) doesn't prove the pattern works for multiple backends.

**User Value**:
- Developers managing larger projects (100+ tasks) get efficient querying
- Transactional operations eliminate inconsistent states from partial failures
- Indexed queries (by status, project_id, created_at) provide instant filtering

**Minimal Complexity**: SQLite requires no external services, no network, no additional deployment complexity—only a file per project.

## What Changes

- **ADDED**: `packages/tasky-storage/src/tasky_storage/backends/sqlite/` module implementing SQLite backend
  - SqliteTaskRepository class implementing TaskRepository protocol
  - Schema creation with indexed tasks table
  - Connection pooling with WAL mode
  - Full CRUD operations with transactions

- **ADDED**: Self-registration for SQLite backend
  - Factory function `sqlite_factory(path: Path) -> SqliteTaskRepository`
  - Auto-registration in module `__init__.py` to global registry
  - Support for `sqlite://` URI configuration

- **MODIFIED**: `backend-self-registration` spec
  - New requirement: SQLite backend self-registration (matching JSON pattern)
  - Factory method for SqliteTaskRepository

- **MODIFIED**: `backend-registry` spec
  - Updated scenarios to demonstrate multiple backends (sqlite alongside json)

## Proposed Solution

Add SQLite storage backend with:

1. **Database Schema**: Single `tasks` table with indexed columns
2. **Repository Protocol**: Implement `TaskRepository` with transaction support
3. **Query Optimization**: Index on status, project_id, created_at for O(log n) filtering
4. **Auto-Initialization**: Create schema on first use
5. **Configuration**: URI-based `sqlite://<path>` configuration
6. **Self-Registration**: Register with global backend registry on import

### User-Facing Changes

```bash
# Existing JSON backend (unchanged)
tasky project init --storage json://.tasky/tasks.json

# New SQLite backend
tasky project init --storage sqlite://.tasky/tasks.db

# List available backends
tasky config list-backends  # shows: json, sqlite
```

## Acceptance Criteria

1. SQLite backend implements full `TaskRepository` protocol
2. All existing tests pass (no breaking changes to public interfaces)
3. Supports efficient querying by status (from existing filtering feature)
4. Auto-initializes database schema on first use
5. Transactions: create/update/delete operations are atomic
6. Registered with backend registry on import
7. Connections use connection pooling (thread-safe)
8. Handles concurrent access safely (database locking)
9. Test coverage ≥80% for SQLite backend
10. Schema supports future filtering (project_id, created_at indexed)

## Non-Goals

- Migrations from JSON to SQLite (manual export/import)
- Multi-database replication or clustering
- Query DSL or ORM (direct SQL via repository)
- Backup automation (users manage database files)
- Performance benchmarking/optimization (suitable for projects up to 1M+ tasks)

## Dependencies

This change depends on:
- `backend-registry` spec (registry pattern already implemented)
- `backend-self-registration` spec (pattern for factories; will extend to SQLite)
- `add-task-filtering` (filtering must work with SQLite)
- `task-timestamp-management` (created_at, updated_at fields for schema)

## Risks and Mitigations

**Risk**: SQLite connection lifecycle management
**Mitigation**: Use connection pooling with contextmanager patterns; validate in tests

**Risk**: Schema migrations when TaskModel changes
**Mitigation**: Document manual migration steps; version schema with comments

**Risk**: File-based database corruption
**Mitigation**: Use PRAGMA integrity_check; document backup strategy

**Risk**: Transaction isolation edge cases
**Mitigation**: Test concurrent create/update/delete with multiple threads

## Alternatives Considered

1. **PostgreSQL backend**: Requires external service; overkill for single-user projects
2. **Async SQLite (aiosqlite)**: Adds async complexity; synchronous repository protocol makes this moot
3. **ORM (SQLAlchemy)**: Unnecessary abstraction over TaskModel; direct SQL keeps code simple
4. **Embedded DuckDB**: Experimental; SQLite proven and familiar

## Implementation Notes

- Database file located at configured path (e.g., `.tasky/tasks.db`)
- Schema created on first `initialize()` call
- No migrations needed; schema is stable for TaskModel
- Connection pooling with max 5 connections per process
- Use write-ahead logging (WAL) mode for better concurrency
- Pragma settings for foreign keys, synchronous mode

## Related Capabilities

This change extends:
- `backend-registry`: SQLite registers alongside JSON
- `backend-self-registration`: SQLite self-registers on import
- `task-timestamp-management`: Uses created_at/updated_at for schema

This enables future work:
- Date-range filtering (queries on created_at efficiently)
- Archived task queries (indexed status filtering)
- Backup/restore tooling (database backup)

## Architecture Alignment

The implementation follows the clean architecture:
- **Domain** (`tasky-tasks`): No changes; `TaskRepository` protocol unchanged
- **Storage** (`tasky-storage`): New `backends/sqlite/` module implementing protocol
- **Hooks**: Optional SQLite-specific hooks (future: schema migration events)
- **Settings** (`tasky-settings`): Recognize `sqlite://` URI; wire SQLite factory
- **CLI** (`tasky-cli`): Support `--storage sqlite://path` in project init

## Success Metrics

1. All existing tests pass unmodified
2. SQLite-specific tests (50+) all pass
3. Filtering by status works efficiently with SQLite (query explains indexed plan)
4. Concurrent create/update/delete operations maintain consistency
5. New project initialized with SQLite works identically to JSON project
