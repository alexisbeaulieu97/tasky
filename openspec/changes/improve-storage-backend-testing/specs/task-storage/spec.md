## MODIFIED Requirements

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
