# task-import-capability Specification

## Purpose
TBD - created by archiving change add-task-import-export. Update Purpose after archive.
## Requirements
### Requirement: Import Tasks from JSON File

The system SHALL provide functionality to import tasks from a JSON file into the current project.

**Rationale**: Users need to restore backups, migrate data between projects, and load task templates. Robust import validation prevents data corruption from malformed files.

#### Scenario: Import with default append strategy

**GIVEN** an exported task JSON file with 10 tasks
**AND** the current project has 5 existing tasks
**WHEN** user executes `tasky task import backup.json`
**THEN** all 10 tasks from the file MUST be imported
**AND** the existing 5 tasks MUST remain unchanged
**AND** the system MUST show "✓ Import complete: 10 created, 0 updated"

#### Scenario: Import requires valid JSON format

**GIVEN** a file with malformed JSON (missing quotes, trailing commas, etc.)
**WHEN** user attempts to import
**THEN** an error MUST be raised with type `InvalidExportFormatError`
**AND** the error message MUST describe the JSON syntax problem
**AND** NO tasks MUST be added to the project
**AND** the user MUST see error: "✗ Invalid file format: Invalid JSON..."

#### Scenario: Import requires compatible version

**GIVEN** an export file with version "2.0" (incompatible future version)
**WHEN** user attempts to import
**THEN** an error MUST be raised with type `IncompatibleVersionError`
**AND** the error message MUST indicate the version mismatch
**AND** NO tasks MUST be added to the project
**AND** the user MUST see error: "✗ Incompatible format version: 2.0"

#### Scenario: Import validates all task fields

**GIVEN** a JSON file with incomplete task data (missing "details" field)
**WHEN** user attempts to import
**THEN** an error MUST be raised with type `TaskValidationError`
**AND** the error message MUST indicate which field is missing
**AND** NO tasks MUST be added to the project

#### Scenario: Import shows summary of results

**GIVEN** successful import completes
**WHEN** import finishes
**THEN** the system MUST display summary in format: "X created, Y updated, Z skipped"
**AND** X MUST be number of new tasks created
**AND** Y MUST be number of existing tasks updated
**AND** Z MUST be number of tasks skipped (if any)

### Requirement: Import Append Strategy

The system SHALL support append strategy that adds imported tasks to existing tasks without modification.

**Rationale**: Users need to merge task lists from multiple sources without losing existing data.

#### Scenario: Append strategy handles duplicate IDs

**GIVEN** export file contains task with ID "abc-123"
**AND** project already has task with ID "abc-123"
**WHEN** import with append strategy executes
**THEN** the existing task MUST remain unchanged
**AND** a NEW task MUST be created with the imported data
**AND** the new task MUST have a newly generated UUID
**AND** both tasks MUST now exist in the project

#### Scenario: Append strategy is default

**GIVEN** user runs `tasky task import file.json` without --strategy flag
**WHEN** import executes
**THEN** append strategy MUST be used by default
**AND** behavior MUST match explicit `--strategy append`

### Requirement: Import Replace Strategy

The system SHALL support replace strategy that clears all existing tasks before importing.

**Rationale**: Users need to perform full backup restoration or migrate complete task list.

#### Scenario: Replace strategy clears existing tasks

**GIVEN** project has 100 existing tasks
**AND** export file has 50 tasks
**WHEN** user executes `tasky task import backup.json --strategy replace`
**THEN** all 100 existing tasks MUST be deleted first
**AND** all 50 tasks from file MUST be imported
**AND** project MUST end with exactly 50 tasks

#### Scenario: Replace strategy shows created count only

**GIVEN** import with replace strategy completes
**WHEN** results are displayed
**THEN** summary MUST show "X created, 0 updated"
**AND** created count MUST match number of imported tasks

### Requirement: Import Merge Strategy

The system SHALL support merge strategy that updates existing tasks by ID and creates new ones.

**Rationale**: Users need to sync task lists between instances, with selective updates for modified tasks.

#### Scenario: Merge strategy updates by task ID

**GIVEN** export file has task with ID "abc-123" and name "Updated Task"
**AND** project has task with ID "abc-123" and name "Original Task"
**WHEN** import with merge strategy executes
**THEN** the task with ID "abc-123" MUST be updated
**AND** the name MUST change to "Updated Task"
**AND** the updated_at timestamp MUST be set to import file's value
**AND** one updated task MUST be counted

#### Scenario: Merge strategy creates new tasks

**GIVEN** export file has task with ID "xyz-789" (not in project)
**WHEN** import with merge strategy executes
**THEN** a new task with ID "xyz-789" MUST be created
**AND** one created task MUST be counted

#### Scenario: Merge strategy combines create and update

**GIVEN** export file with 20 tasks, 15 already in project by ID
**WHEN** import with merge strategy executes
**THEN** 15 tasks MUST be updated
**AND** 5 tasks MUST be created
**AND** summary MUST show "5 created, 15 updated"

### Requirement: Dry-Run Mode

The system SHALL support dry-run mode that shows import preview without applying changes.

**Rationale**: Users need to preview import impact before committing data changes.

#### Scenario: Dry-run shows preview without changes

**GIVEN** export file with 10 tasks
**AND** project has 5 existing tasks
**WHEN** user executes `tasky task import backup.json --dry-run`
**THEN** system MUST show what WOULD happen: "10 created, 0 updated"
**AND** NO tasks MUST actually be added to the project
**AND** the 5 existing tasks MUST remain unchanged
**AND** message MUST indicate preview mode: "[DRY RUN] Would import: ..."

#### Scenario: Dry-run works with all strategies

**GIVEN** user specifies different strategy with dry-run
**WHEN** import executes
**THEN** dry-run MUST show preview for that specific strategy
**AND** replace strategy preview shows existing count BEFORE deletion
**AND** merge strategy preview shows create/update breakdown

---

