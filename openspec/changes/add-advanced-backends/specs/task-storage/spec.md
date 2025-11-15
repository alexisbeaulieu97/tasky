## ADDED Requirements

### Requirement: PostgreSQL Storage Backend

The system SHALL support PostgreSQL as a storage backend, enabling multi-user, enterprise-grade task management with concurrent access, audit trails, and scalability.

#### Scenario: PostgreSQL backend stores tasks
- **GIVEN** a project configured to use PostgreSQL backend
- **WHEN** tasks are created, updated, deleted
- **THEN** all operations are persisted to PostgreSQL
- **AND** operations are immediately visible to other clients
- **AND** data survives server restart

#### Scenario: Concurrent access is safe
- **WHEN** multiple clients access the same project simultaneously
- **THEN** concurrent reads work without conflict
- **AND** concurrent writes are serialized or detected
- **AND** data consistency is guaranteed (no lost updates)
- **AND** error is returned if write conflict occurs

#### Scenario: PostgreSQL backend uses transactions
- **GIVEN** a multi-step operation (create task, then update, then complete)
- **WHEN** all steps succeed
- **THEN** all changes are committed atomically
- **AND** if any step fails, all changes are rolled back
- **AND** partial updates are never visible

#### Scenario: Schema is created automatically
- **GIVEN** first connection to a PostgreSQL database for a project
- **WHEN** no schema exists yet
- **THEN** schema is created automatically (migrations run)
- **AND** tables, indexes, constraints are set up
- **AND** database is ready for use

#### Scenario: Schema migrations support upgrades
- **GIVEN** existing PostgreSQL database from v1.0
- **WHEN** upgrading tasky to v1.1
- **THEN** migration runs automatically
- **AND** schema is upgraded safely
- **AND** existing data is preserved
- **AND** old schema can be rolled back if needed

### Requirement: Audit Trail

The PostgreSQL backend SHALL maintain an audit trail of all task operations, recording who changed what and when.

#### Scenario: Task creation is audited
- **WHEN** a task is created
- **THEN** audit log records the creation
- **AND** timestamp, task_id, creator, and initial values are logged
- **AND** audit log is immutable (append-only)

#### Scenario: Task updates are fully audited
- **WHEN** a task is updated
- **THEN** audit log records the change
- **AND** timestamp, task_id, modifier, old value, and new value are logged
- **AND** field-level changes can be tracked

#### Scenario: Audit trail is queryable
- **WHEN** user requests history for a task
- **THEN** full change history is returned
- **AND** changes are in chronological order
- **AND** each entry shows who made the change and when

### Requirement: Configuration & Connection Management

The PostgreSQL backend SHALL be configurable and manage database connections efficiently.

#### Scenario: PostgreSQL is configured via connection string
- **GIVEN** environment variable `DATABASE_URL=postgresql://user:pass@host:5432/db`
- **WHEN** project is initialized with PostgreSQL backend
- **THEN** connection uses the provided URL
- **AND** all tasks are stored in that database

#### Scenario: Connection pool prevents exhaustion
- **GIVEN** many concurrent connections to PostgreSQL
- **WHEN** connection pool is configured (min=5, max=20)
- **THEN** max 20 connections are created
- **AND** idle connections are recycled
- **AND** long-running queries don't prevent other operations

#### Scenario: Database becomes unavailable gracefully
- **WHEN** PostgreSQL server is down
- **THEN** error is returned (not infinite hang)
- **AND** error message indicates database unavailable
- **AND** retry logic can be configured
- **AND** graceful degradation is possible (if needed)

### Requirement: Multi-Backend Compatibility

PostgreSQL backend SHALL implement the same `TaskRepository` protocol as JSON and SQLite, ensuring identical behavior.

#### Scenario: All backends produce identical results
- **GIVEN** same task operations against JSON, SQLite, and PostgreSQL backends
- **WHEN** operations complete
- **THEN** final task state is identical across all backends
- **AND** all task fields match exactly
- **AND** all timestamps match (within rounding)

#### Scenario: Backend switching preserves data
- **GIVEN** tasks in SQLite backend
- **WHEN** migrating to PostgreSQL backend
- **THEN** all tasks are copied to PostgreSQL
- **AND** task IDs remain unchanged
- **AND** all fields are preserved
- **AND** timestamps are preserved
