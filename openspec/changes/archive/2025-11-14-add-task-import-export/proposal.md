# Proposal: Add Task Import/Export Functionality

**Change ID**: `add-task-import-export`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal introduces comprehensive task import/export capabilities to enable backup, restore, migration, and sharing of task collections. Currently, users cannot backup their tasks, migrate between projects, or share task templates with others. This change adds JSON-based import/export with multiple strategies and robust conflict resolution.

## Problem Statement

Users face several critical gaps in task portability and data management:

1. **No Backup/Restore**: Tasks are stored only in the project directory with no easy way to create backups for disaster recovery
2. **No Migration Path**: Users cannot move tasks between projects or storage backends
3. **No Template Sharing**: Teams cannot share task lists or create task templates
4. **Data Lock-in**: Tasks are bound to a single project with no export capability
5. **Disaster Recovery**: Loss of `.tasky/` directory means permanent data loss

## Why

Task import/export addresses a fundamental need in task management systems:

- **Business Continuity**: Users need backup and restore for disaster recovery
- **Portability**: Users should be able to move tasks between projects and machines
- **Collaboration**: Teams need to share task templates and collaborate on task lists
- **Data Ownership**: Users should have easy access to their data in portable formats
- **Integration**: Export capability enables integration with other tools and analysis

Without import/export, tasky is a black-box data silo. Users cannot backup their work, share task lists, or migrate data if requirements change.

## What Changes

- **NEW**: `TaskImportExportService` class with export/import methods
- **NEW**: Four new CLI commands: `tasky task export`, `tasky task import`
- **NEW**: Three import merge strategies: append (default), replace, merge
- **NEW**: Pydantic models for export schema validation
- **NEW**: Import exceptions for error handling
- **MODIFIED**: CLI task commands to include new export/import commands

## Proposed Solution

Add JSON-based import/export with three merge strategies:

### User-Facing Commands

```bash
# Export all tasks to JSON file
tasky task export tasks-backup.json

# Export specific tasks
tasky task export --filter completed backup-completed.json

# Import with append strategy (default - adds to existing)
tasky task import tasks-backup.json
tasky task import tasks-backup.json --strategy append

# Import with replace strategy (clears all first)
tasky task import tasks-backup.json --strategy replace

# Import with merge strategy (updates existing by ID)
tasky task import tasks-backup.json --strategy merge

# Show import preview without applying
tasky task import tasks-backup.json --dry-run
```

### Export Format

```json
{
  "version": "1.0",
  "exported_at": "2025-11-12T10:30:00Z",
  "source_project": "default",
  "task_count": 42,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Implement task filtering",
      "details": "Add status filtering to task list command",
      "status": "completed",
      "created_at": "2025-11-11T08:00:00Z",
      "updated_at": "2025-11-12T10:00:00Z"
    },
    {
      "task_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Fix task persistence bug",
      "details": "JSON storage not persisting newly created tasks",
      "status": "pending",
      "created_at": "2025-11-12T09:30:00Z",
      "updated_at": "2025-11-12T09:30:00Z"
    }
  ]
}
```

### Import Strategies

1. **Append (default)**: Adds imported tasks to existing tasks. If task with same ID exists, creates new task with new ID instead.

2. **Replace**: Clears all existing tasks first, then imports. Useful for full backup restore or migrations.

3. **Merge**: Updates tasks by ID if they exist, creates new tasks if they don't. Useful for syncing task lists.

## Impact

- **Affected specs**:
  - `task-export` (new capability)
  - `task-import` (new capability)
  - `task-import-strategies` (new capability)
  - `task-import-export-cli` (new capability)
- **Affected code**:
  - `packages/tasky-tasks/src/tasky_tasks/export.py` (new)
  - `packages/tasky-tasks/src/tasky_tasks/exceptions.py` (modified)
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` (modified)
- **New dependencies**: Pydantic (already in use)
- **Breaking changes**: None

## Acceptance Criteria

1. CLI provides `tasky task export FILE` command
2. Export creates JSON file with version, metadata, task count, and tasks array
3. Export JSON includes all task fields (id, name, details, status, created_at, updated_at)
4. CLI provides `tasky task import FILE` command with `--strategy` option
5. Strategies work correctly:
   - **Append**: Creates new tasks, preserves existing tasks
   - **Replace**: Clears all first, then imports
   - **Merge**: Updates by ID, creates if not found
6. Import validates JSON file format before applying changes
7. Import shows summary: "X created, Y updated, Z skipped"
8. `--dry-run` flag shows preview without applying
9. Invalid JSON files produce helpful error messages
10. Incompatible format versions are detected and rejected
11. Empty export files are handled gracefully
12. Large files (1000+ tasks) are imported efficiently

## Non-Goals

- Incremental/differential backups (full export only)
- Encrypted exports (add if security requirement emerges)
- Streaming large files (load entire file in memory for now)
- Format conversion (JSON only, not CSV/XML)
- S3/cloud storage integration (local files only)
- Scheduled/automatic backups (manual exports for now)
- Conflict resolution UI (silent merge strategy for now)
- Import rollback (separate feature if needed)

## Dependencies

This change depends on:
- `add-task-state-transitions` (for task status consistency)
- `add-automatic-timestamps` (for created_at/updated_at)

## Risks and Mitigations

**Risk**: Replace strategy could accidentally delete all tasks
**Mitigation**: Require explicit `--strategy replace` flag; show confirmation prompt; backup capability allows recovery.

**Risk**: Large task counts could cause memory issues during import
**Mitigation**: JSON file is loaded once; for >100k tasks, recommend streaming approach in future.

**Risk**: Merge strategy conflicts (task exists with different data)
**Mitigation**: Import summary shows what was created/updated/skipped; no silent overwrites without --strategy merge.

**Risk**: Format version incompatibility in future
**Mitigation**: Version field in export JSON allows forward compatibility checks.

## Alternatives Considered

1. **CSV export**: Simpler but loses structure; JSON preserves type safety
2. **XML export**: More verbose, harder for manual editing
3. **Binary format**: Faster but less portable and human-readable
4. **Streaming import**: Overkill for current task counts; can add later
5. **Auto-backup on every save**: Disk bloat; users should manage backups explicitly

## Implementation Notes

- Export queries all tasks via `service.get_all_tasks()`
- Import parses JSON, validates against schema, applies strategy
- Each strategy is a separate method: `_apply_append_strategy()`, `_apply_replace_strategy()`, `_apply_merge_strategy()`
- Use Pydantic for export schema validation
- Show progress/summary after import completes
- Handle timestamp parsing carefully (UTC, ISO 8601 format)

## Related Changes

- Foundation for future template management
- Enables integration with external tools
- Supports future cloud backup features
- Allows task data analysis and reporting

## Success Metrics

1. Export/import round-trip preserves all task data
2. Merge strategy correctly identifies and updates existing tasks
3. Import validation catches 100% of invalid JSON files
4. User can recover from accidental task deletion via export
5. Performance: import 1000 tasks in <1 second
6. Test coverage ≥80% for all import/export code
