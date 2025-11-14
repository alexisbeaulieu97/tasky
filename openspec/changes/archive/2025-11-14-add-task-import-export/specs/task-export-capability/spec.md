# Spec: Task Export Capability

**Capability**: `task-export`
**Status**: Draft
**Package**: `tasky-tasks`
**Layer**: Domain + Presentation

## Overview

Defines the requirements for exporting tasks to JSON format with comprehensive metadata and structure. The export capability allows users to backup their tasks, migrate between projects, and share task lists.

---

## ADDED Requirements

### Requirement: Export Tasks to JSON File

The system SHALL provide functionality to export all tasks to a JSON file with structured format.

**Rationale**: Users need to backup their tasks and migrate data between projects. JSON format ensures portability and human readability.

#### Scenario: Export creates valid JSON file

**GIVEN** a project with multiple tasks of different statuses
**WHEN** user executes `tasky task export backup.json`
**THEN** a JSON file MUST be created at the specified path
**AND** the file MUST contain valid JSON parseable by standard JSON parsers
**AND** the file MUST NOT contain syntax errors

#### Scenario: Export file contains required metadata

**GIVEN** an export operation completes successfully
**WHEN** the exported JSON file is examined
**THEN** it MUST contain a "version" field with value "1.0"
**AND** it MUST contain an "exported_at" timestamp in ISO 8601 UTC format
**AND** it MUST contain a "source_project" identifier
**AND** it MUST contain a "task_count" field matching the number of tasks exported
**AND** all fields MUST be at the top level of the JSON object

#### Scenario: Export preserves all task fields

**GIVEN** tasks in the project with various attributes
**WHEN** tasks are exported to JSON
**THEN** each task MUST include "task_id" as UUID string
**AND** each task MUST include "name" as string
**AND** each task MUST include "details" as string
**AND** each task MUST include "status" as one of: pending, completed, cancelled
**AND** each task MUST include "created_at" timestamp in ISO 8601 UTC format
**AND** each task MUST include "updated_at" timestamp in ISO 8601 UTC format

#### Scenario: Export handles empty task list

**GIVEN** a project with no tasks
**WHEN** user exports to JSON
**THEN** a valid JSON file MUST be created
**AND** the "task_count" field MUST be 0
**AND** the "tasks" array MUST be empty

#### Scenario: Export timestamps use UTC timezone

**GIVEN** tasks with various timestamps
**WHEN** tasks are exported
**THEN** all timestamps MUST be in ISO 8601 format with UTC designation
**AND** timestamps MUST end with 'Z' suffix or '+00:00' indicating UTC
**AND** all timestamps MUST be timezone-aware and comparable

#### Scenario: Export file is human-readable

**GIVEN** an exported JSON file
**WHEN** the file is opened in a text editor
**THEN** the JSON MUST be formatted with indentation for readability
**AND** the structure MUST be understandable without specialized tools
**AND** task data MUST be easily identifiable

---

## Implementation Notes

- Export function: `TaskImportExportService.export_tasks(file_path: Path) -> ExportDocument`
- Located in: `packages/tasky-tasks/src/tasky_tasks/export.py`
- Creates parent directory if needed: `file_path.parent.mkdir(parents=True, exist_ok=True)`
- Uses `json.dumps(..., indent=2)` for human-readable formatting
- Timestamp format: ISO 8601 with UTC (e.g., "2025-11-12T10:30:00Z")
- Export includes ALL tasks (no filtering at this stage)

---

## Testing Requirements

### Unit Tests
- Export with mixed task statuses produces valid JSON
- Metadata fields (version, exported_at, task_count) are correct
- All task fields preserved accurately
- Empty task list handled gracefully
- Timestamps in correct UTC ISO 8601 format
- JSON is properly indented and human-readable

### Integration Tests
- Exported file can be parsed by standard JSON parser
- Round-trip: export → parse → compare with original
- File permissions preserved after write
- Parent directory created if missing

---

## Related Specifications

- `task-import`: Complementary import capability
- `task-import-strategies`: Different merge strategies for import
- Relies on: `task-state-transitions` (for TaskStatus values)
- Relies on: `automatic-timestamps` (for created_at/updated_at fields)

