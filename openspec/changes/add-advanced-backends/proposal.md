# Change: Add Advanced Storage Backends (PostgreSQL)

## Why

Tasky currently supports JSON (single-user local) and SQLite (better for power users). Enterprise and collaborative use cases require:

- **PostgreSQL backend**: Multi-user, concurrent access, shared task databases
- **Cloud synchronization**: Share tasks across devices
- **Backup & recovery**: Enterprise-grade data protection
- **Audit trails**: Track who changed what and when
- **Scalability**: Support thousands of users with millions of tasks

Implementing PostgreSQL validates the backend abstraction (adding new backends becomes "just an implementation" of the existing protocol).

## What Changes

- Create `packages/tasky-storage/backends/postgresql/` backend implementation
- Implement PostgreSQL connection management (psycopg2/asyncpg)
- Create database schema (migrations using Alembic)
- Implement all `TaskRepository` protocol methods for PostgreSQL
- Add multi-user support (project ownership, access control)
- Implement concurrent access handling (pessimistic locking for conflicts)
- Add configuration for PostgreSQL connection (URL, credentials, pool size)
- Create comprehensive tests (unit + integration against real PostgreSQL)

## Impact

- **Affected specs**: Extends `task-storage` spec with PostgreSQL requirements
- **Affected code**: New `packages/tasky-storage/backends/postgresql/`, settings updates
- **Backward compatibility**: Fully additive; existing backends unaffected
- **Dependencies**: Adds `psycopg2-binary` or `asyncpg` for database connectivity
- **Feature**: Multi-user, enterprise-grade task management
