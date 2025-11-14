# task-import-strategies Specification

## Purpose
TBD - created by archiving change add-task-import-export. Update Purpose after archive.
## Requirements
### Requirement: Append Import Strategy

The system SHALL implement append strategy that adds imported tasks without conflict resolution.

**Rationale**: Users need a simple way to merge task lists from multiple sources, especially templates.

#### Scenario: Append adds all imported tasks

**GIVEN** project has 3 existing tasks (IDs: A, B, C)
**AND** export file has 2 tasks (IDs: X, Y)
**WHEN** import with append strategy executes
**THEN** task X MUST be created unchanged
**AND** task Y MUST be created unchanged
**AND** project MUST have 5 total tasks
**AND** original tasks A, B, C MUST remain unchanged

#### Scenario: Append re-keys duplicate IDs

**GIVEN** project has task with ID "abc-123"
**AND** export file has different task with ID "abc-123"
**WHEN** import with append strategy executes
**THEN** the original task "abc-123" MUST remain unchanged
**AND** the imported task MUST be assigned a new UUID
**AND** the newly assigned UUID MUST not conflict with any existing task
**AND** the imported task's data MUST be preserved (name, details, status, timestamps)

#### Scenario: Append preserves import timestamps

**GIVEN** exported task with created_at = "2025-01-01T00:00:00Z"
**WHEN** import with append strategy adds the task
**THEN** the imported task MUST retain created_at = "2025-01-01T00:00:00Z"
**AND** the task MUST NOT have its timestamps modified

#### Scenario: Append result shows only created count

**GIVEN** import with append strategy completes
**WHEN** result is calculated
**THEN** ImportResult MUST show: created = N, updated = 0, skipped = 0
**AND** N MUST equal the number of imported tasks

### Requirement: Replace Import Strategy

The system SHALL implement replace strategy that clears all existing tasks before importing.

**Rationale**: Users need full backup restoration capability with no risk of duplicates.

#### Scenario: Replace deletes all existing tasks

**GIVEN** project has 100 existing tasks
**WHEN** import with replace strategy starts
**THEN** all 100 existing tasks MUST be deleted from storage
**AND** deletion MUST complete before any imported tasks are added

#### Scenario: Replace imports all new tasks

**GIVEN** replace strategy has cleared project
**AND** export file has 50 tasks
**WHEN** import continues
**THEN** all 50 tasks from file MUST be added
**AND** each task MUST have exactly the data from export file
**AND** no modifications MUST be made to imported task IDs or data

#### Scenario: Replace produces final state

**GIVEN** replace strategy completes successfully
**WHEN** result is examined
**THEN** project MUST have exactly N tasks (from export file)
**AND** no original tasks MUST remain
**AND** ImportResult MUST show: created = N, updated = 0, skipped = 0

#### Scenario: Replace handles empty import

**GIVEN** export file is empty (task_count = 0)
**WHEN** import with replace strategy executes
**THEN** all existing tasks MUST be deleted
**AND** no tasks MUST be added
**AND** project MUST be empty

### Requirement: Merge Import Strategy

The system SHALL implement merge strategy that updates tasks by ID and creates new ones.

**Rationale**: Users need to sync task lists between instances with selective updates.

#### Scenario: Merge updates task when ID exists

**GIVEN** project has task ID="abc-123" with name="Old Name"
**AND** export file has task ID="abc-123" with name="New Name"
**WHEN** import with merge strategy executes
**THEN** task "abc-123" MUST be updated
**AND** task name MUST change to "New Name"
**AND** task updated_at MUST be set to imported value
**AND** status and other fields MUST match imported values

#### Scenario: Merge creates task when ID is new

**GIVEN** project has no task with ID "xyz-789"
**AND** export file has task ID="xyz-789"
**WHEN** import with merge strategy executes
**THEN** task with ID="xyz-789" MUST be created
**AND** task data MUST exactly match export file
**AND** no fields MUST be modified from import

#### Scenario: Merge preserves unaffected existing tasks

**GIVEN** project has task ID="keep-me-123" not in export file
**WHEN** import with merge strategy executes
**THEN** task "keep-me-123" MUST remain unchanged
**AND** not counted in updated or created counts
**AND** task MUST still exist in project after import

#### Scenario: Merge tracks created, updated, skipped

**GIVEN** export file with 20 tasks:
  - 15 with IDs matching existing tasks
  - 5 with IDs not in project
**WHEN** import with merge strategy executes
**THEN** ImportResult MUST show: created = 5, updated = 15, skipped = 0

#### Scenario: Merge updates all imported fields

**GIVEN** existing task and imported task with same ID but different values
**WHEN** merge updates the task
**THEN** all fields MUST be updated:
  - name MUST change
  - details MUST change
  - status MUST change
  - updated_at MUST change
  - created_at MUST NOT change (original preserved)

### Requirement: Strategy Parameter Validation

The system SHALL validate strategy parameter and reject invalid values.

**Rationale**: Users need clear feedback for incorrect strategy names.

#### Scenario: Valid strategy values accepted

**GIVEN** user specifies strategy value
**WHEN** value is one of: "append", "replace", "merge"
**THEN** strategy MUST be accepted
**AND** import MUST proceed with specified strategy

#### Scenario: Invalid strategy rejected

**GIVEN** user specifies strategy value "invalid"
**WHEN** import validates strategy
**THEN** error MUST be raised
**AND** error message MUST list valid strategies: "append, replace, merge"
**AND** import MUST NOT execute
**AND** user MUST see: "✗ Invalid strategy 'invalid'. Valid: append, replace, merge"

#### Scenario: Strategy is case-insensitive

**GIVEN** user specifies strategy "APPEND" or "Append"
**WHEN** import validates
**THEN** strategy MUST be recognized as "append"
**AND** import MUST proceed normally

---

