# task-import-export-cli Specification

## Purpose
TBD - created by archiving change add-task-import-export. Update Purpose after archive.
## Requirements
### Requirement: Export CLI Command

The system SHALL provide `tasky task export` command that exports all tasks to a JSON file.

**Rationale**: Users need accessible command-line interface for backup creation.

#### Scenario: Export command with file path argument

**GIVEN** user wants to backup tasks
**WHEN** user executes `tasky task export backup.json`
**THEN** command MUST accept a file path as positional argument
**AND** export MUST create file at specified path
**AND** file MUST contain valid JSON with all tasks
**AND** system MUST display: "✓ Exported 42 tasks to backup.json"

#### Scenario: Export creates parent directory if needed

**GIVEN** file path is `backups/2025-11-12/tasks.json`
**AND** directory `backups/2025-11-12/` does not exist
**WHEN** user executes export
**THEN** parent directories MUST be created automatically
**AND** file MUST be written successfully

#### Scenario: Export shows success message

**GIVEN** export completes successfully
**WHEN** user sees output
**THEN** message MUST start with green checkmark: "✓"
**AND** message MUST include file path: "...to backup.json"
**AND** message MUST show task count: "Exported 42 tasks..."

#### Scenario: Export handles I/O errors

**GIVEN** file path is not writable (permission denied)
**WHEN** user executes export
**THEN** error MUST be shown: "✗ Cannot write to file..."
**AND** error MUST be user-friendly and actionable
**AND** no partial file MUST be left

#### Scenario: Export command help is helpful

**GIVEN** user runs `tasky task export --help`
**WHEN** help is displayed
**THEN** help MUST show:
  - Description of export functionality
  - File path argument documentation
  - Example: `tasky task export backup.json`
  - Note about JSON format

### Requirement: Import CLI Command

The system SHALL provide `tasky task import` command that imports tasks from a JSON file.

**Rationale**: Users need accessible command-line interface for backup restoration.

#### Scenario: Import command with file path argument

**GIVEN** user has backup file `backup.json`
**WHEN** user executes `tasky task import backup.json`
**THEN** command MUST accept file path as positional argument
**AND** import MUST read and validate file
**AND** import MUST use append strategy by default
**AND** system MUST display summary: "✓ Import complete: 10 created, 0 updated"

#### Scenario: Import accepts --strategy option

**GIVEN** user wants specific merge strategy
**WHEN** user executes `tasky task import file.json --strategy replace`
**THEN** command MUST accept --strategy option with value
**AND** valid values MUST be: append, replace, merge
**AND** specified strategy MUST be used for import

#### Scenario: Import accepts short option -S

**GIVEN** user prefers short flags
**WHEN** user executes `tasky task import file.json -S merge`
**THEN** short option MUST work identically to --strategy
**AND** behavior MUST be identical

#### Scenario: Import default strategy is append

**GIVEN** user runs import without --strategy flag
**WHEN** import executes
**THEN** append strategy MUST be used by default
**AND** message MUST indicate strategy used (optional)

#### Scenario: Import accepts --dry-run flag

**GIVEN** user wants to preview import impact
**WHEN** user executes `tasky task import file.json --dry-run`
**THEN** import MUST validate file
**AND** import MUST calculate what WOULD happen
**AND** NO tasks MUST be added
**AND** system MUST display: "[DRY RUN] Would import: 10 created, 0 updated"

#### Scenario: Import shows summary result

**GIVEN** import completes successfully
**WHEN** user sees output
**THEN** message format MUST be: "✓ Import complete: X created, Y updated"
**AND** X MUST be number of created tasks
**AND** Y MUST be number of updated tasks
**AND** message MUST start with green checkmark

#### Scenario: Import handles missing file

**GIVEN** file path `missing.json` does not exist
**WHEN** user executes import
**THEN** error MUST be shown: "✗ File not found: missing.json"
**AND** error MUST be helpful
**AND** no import MUST occur

#### Scenario: Import handles invalid JSON

**GIVEN** file contains malformed JSON
**WHEN** user executes import
**THEN** error MUST be shown: "✗ Invalid file format: ..."
**AND** error details MUST help user fix the problem
**AND** no tasks MUST be added

#### Scenario: Import handles incompatible version

**GIVEN** export file has version "2.0"
**WHEN** user executes import
**THEN** error MUST be shown: "✗ Incompatible format version: 2.0"
**AND** user MUST be told current version supported
**AND** no tasks MUST be added

#### Scenario: Import handles invalid strategy

**GIVEN** user specifies strategy "invalid"
**WHEN** user executes import
**THEN** error MUST be shown: "✗ Invalid strategy 'invalid'"
**AND** valid strategies MUST be listed: "append, replace, merge"
**AND** import MUST NOT execute

#### Scenario: Import command help is helpful

**GIVEN** user runs `tasky task import --help`
**WHEN** help is displayed
**THEN** help MUST show:
  - Description of import functionality
  - File path argument documentation
  - All strategy options with explanations
  - Dry-run flag documentation
  - Examples of each strategy:
    - `tasky task import backup.json`
    - `tasky task import backup.json --strategy replace`
    - `tasky task import backup.json --dry-run`

---

