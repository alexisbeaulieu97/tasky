## ADDED Requirements

### Requirement: Shared Storage Utilities

The tasky-storage package SHALL provide shared utility functions for common operations needed by all backends, eliminating code duplication and ensuring consistency.

#### Scenario: Snapshot conversion is unified
- **GIVEN** a storage backend needs to convert a snapshot to TaskModel
- **WHEN** the backend calls the shared conversion utility
- **THEN** conversion uses the same logic regardless of backend type
- **AND** error handling is consistent across all backends
- **AND** all task fields are properly deserialized

#### Scenario: Serialization is standardized
- **GIVEN** different backends need to serialize TaskModel objects
- **WHEN** backends use Pydantic's mode="json" serialization
- **THEN** datetime and enum values are serialized identically
- **AND** output format is consistent across JSON and SQLite backends
- **AND** serialized data is re-parseable into identical TaskModel

### Requirement: Backend Implementation Consistency

All storage backends SHALL implement core operations identically, with differences only in storage mechanism.

#### Scenario: Error handling is identical
- **GIVEN** a snapshot conversion error occurs
- **WHEN** the error is raised by the shared utility
- **THEN** all backends handle the error identically
- **AND** error messages are consistent across backends
- **AND** error recovery is identical

#### Scenario: Backends are functionally equivalent
- **GIVEN** a sequence of operations (create, read, filter, update, delete)
- **WHEN** the same sequence runs against both JSON and SQLite backends
- **THEN** final state is identical
- **AND** all tasks have identical field values
- **AND** all timestamps match
