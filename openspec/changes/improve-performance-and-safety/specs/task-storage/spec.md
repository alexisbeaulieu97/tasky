## MODIFIED Requirements

### Requirement: Efficient Task Filtering

The storage backend SHALL filter tasks efficiently, avoiding unnecessary conversions for large datasets. Filtering performance SHALL scale sub-linearly with dataset size.

#### Scenario: Filtering large dataset is efficient
- **WHEN** filtering 10,000 tasks by status
- **THEN** filter completes in <100ms (previously could be >1s)
- **AND** memory usage is bounded (not converting all 10k tasks to memory)
- **AND** filtering results are identical to previous implementation

#### Scenario: Complex filters are applied efficiently
- **WHEN** combining multiple filters (status + date range + search)
- **THEN** filters are applied in order from most selective to least selective
- **AND** expensive operations (model conversion) happen only on filtered results
- **AND** performance scales with result set size, not total dataset size

### Requirement: Data Durability and Atomic Writes

The JSON storage backend SHALL provide data durability guarantees. Writes SHALL be atomic: either fully committed or fully rolled back, never partially written.

#### Scenario: Save operation is interrupted mid-write
- **GIVEN** a save operation writing to disk
- **WHEN** the process is terminated or power is lost during write
- **THEN** the existing task file remains unchanged (not corrupted)
- **AND** data is not lost (original state is preserved)
- **AND** new save operation can proceed normally

#### Scenario: Disk becomes full during save
- **GIVEN** a task save operation that runs out of disk space
- **WHEN** the disk is full mid-write
- **THEN** exception is raised immediately
- **AND** original file remains valid (not truncated)
- **AND** no partial writes exist on disk

### Requirement: Registry Scalability

The project registry SHALL efficiently handle large numbers of projects without excessive memory usage.

#### Scenario: Large registry doesn't exhaust memory
- **GIVEN** a registry with 100,000 projects
- **WHEN** listing or searching projects
- **THEN** memory usage remains bounded (<100MB)
- **AND** pagination prevents loading all projects at once
- **AND** queries complete in reasonable time (<1 second)

#### Scenario: Registry size limits are enforced
- **GIVEN** a user attempting to register beyond the maximum project count
- **WHEN** they exceed the configured limit (default 10,000)
- **THEN** a clear warning is shown: "Registry is approaching size limit (9,999/10,000)"
- **AND** users can increase the limit via configuration if needed
- **AND** no data is lost or silently dropped

### Requirement: Reliable Import Error Handling

Import operations SHALL provide clear error diagnostics and fail safely.

#### Scenario: Import error includes task context
- **GIVEN** an import operation with a malformed task in the middle
- **WHEN** the error is encountered
- **THEN** error message includes which task failed: "Failed to import task #5 (id: <uuid>): <specific error>"
- **AND** user knows which task to fix
- **AND** operation fails safely (no partial import)

#### Scenario: Programmer errors are not swallowed
- **GIVEN** an import operation with an unexpected error (TypeError, AttributeError)
- **WHEN** the error is encountered
- **THEN** the exception propagates (not silently logged)
- **AND** developer is alerted to the bug
- **AND** user sees appropriate error message (not Python traceback)
