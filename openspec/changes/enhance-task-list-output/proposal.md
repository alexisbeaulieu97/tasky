# Proposal: Enhance Task List Output

**Change ID**: `enhance-task-list-output`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal enhances the `tasky task list` command to display critical task information that is currently missing: task status indicators, task IDs, and optional timestamps. Currently, users cannot distinguish between pending, completed, and cancelled tasks without additional context, and cannot reference task IDs when using other commands.

## Problem Statement

The current `tasky task list` command displays only task names and details, which creates usability gaps:

- **No status visibility**: Users cannot tell if a task is pending, completed, or cancelled
- **No task IDs**: Users cannot reference specific tasks when using other commands (e.g., `tasky task complete <id>`)
- **No timestamps**: Users cannot see when tasks were created or modified without using dedicated commands
- **Poor task sorting**: Tasks appear in arbitrary order, making it hard to focus on pending work
- **No task count**: Users have no summary of how many tasks match their view

This forces users to either memorize task details or maintain external documentation to track task status and identifiers.

## What Changes

- Task list now displays status indicators (○ for pending, ✓ for completed, ✗ for cancelled)
- Task IDs are shown in UUID format for each task
- Output format changed to: `{status} {id} {name} - {details}`
- New `--long`/`-l` flag shows creation and modification timestamps
- Task list is sorted by status: pending first, completed second, cancelled last
- Summary line displays total task count and breakdown by status
- Help text documents the enhanced output format and new flags

## Why

Task management requires clear visibility into task status and identity. As the task list grows beyond a handful of tasks, the current output becomes inadequate. Users need:

- **Status indicators** to quickly assess what's pending vs completed
- **Task IDs** to interact with other commands that reference specific tasks
- **Timestamps** to understand task history and aging
- **Intelligent sorting** to surface active work first
- **Count summaries** to understand the scope of work

These are fundamental requirements for any task management system and are expected by users coming from tools like `todo.txt`, `taskwarrior`, or GitHub issues.

## Proposed Solution

Enhance the `task list` command with improved output formatting:

1. **Display format**: Show status indicator (○/✓/✗), task ID, name, and details
2. **Optional timestamps**: Add `--long/-l` flag to show creation and modification times
3. **Task count**: Display total number of tasks shown and filtered information
4. **Smart sorting**: Show pending tasks first, then completed, then cancelled
5. **Consistent formatting**: Ensure output is parseable and visually clean

### User-Facing Changes

```bash
# Current output (before)
Task 1 - Details 1
Task 2 - Details 2
Task 3 - Details 3

# New output (after)
○ 550e8400-e29b-41d4-a716-446655440000 Task 1 - Details 1
✓ 550e8400-e29b-41d4-a716-446655440001 Task 2 - Details 2
✗ 550e8400-e29b-41d4-a716-446655440002 Task 3 - Details 3

Showing 3 tasks (3 pending, 0 completed, 0 cancelled)

# With --long/-l flag
○ 550e8400-e29b-41d4-a716-446655440000 Task 1 - Details 1
  Created: 2025-11-12T10:30:00Z | Modified: 2025-11-12T10:30:00Z
✓ 550e8400-e29b-41d4-a716-446655440001 Task 2 - Details 2
  Created: 2025-11-11T14:20:00Z | Modified: 2025-11-12T09:15:00Z
✗ 550e8400-e29b-41d4-a716-446655440002 Task 3 - Details 3
  Created: 2025-11-10T08:00:00Z | Modified: 2025-11-10T08:00:00Z

Showing 3 tasks (3 pending, 0 completed, 0 cancelled)
```

## Acceptance Criteria

1. Task list displays status indicators (○ for pending, ✓ for completed, ✗ for cancelled)
2. Task IDs are displayed in UUID format for each task
3. Output format shows: status, ID, name, and details on same line
4. `--long/-l` flag displays timestamps below each task (when provided)
5. Tasks are sorted: pending first, then completed, then cancelled
6. A summary line shows total count and breakdown by status
7. Summary works correctly with filtering (if status filter already applied)
8. Empty task list shows "No tasks to display"
9. Formatting is consistent and parseable for scripting
10. Help text (`tasky task list --help`) documents new output format

## Impact

- **Affected specs**: `task-cli-operations` (adds Task Listing requirement)
- **Affected code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` (list command formatting)
  - `packages/tasky-cli/tests/` (new tests for formatting and sorting)
- **Breaking changes**: Yes - output format changes (presentation layer only, no API changes)
- **User-facing changes**: All users will see new output format with status indicators and IDs
- **Dependencies**: Requires existing `created_at` and `updated_at` timestamp fields on tasks

## Non-Goals

- Customizable output formats or templates (future enhancement)
- Colored/styled terminal output beyond ASCII symbols (future enhancement)
- Filtering by date range (separate enhancement)
- Task priority or custom field display (future enhancement)
- Configuration file options for default display format (future enhancement)

## Dependencies

This change does **not** create new dependencies but assumes:
- Tasks have `id`, `name`, `details`, `status` fields (already exist)
- Tasks have `created_at` and `updated_at` timestamps (from `task-timestamp-management` spec)
- `TaskStatus` enum with PENDING, COMPLETED, CANCELLED values (already exists)

## Risks and Mitigations

**Risk**: Output format change could break existing scripts or CI/CD workflows that parse task list output
**Mitigation**:
- New format is backwards-incompatible by design (necessary for usability)
- Consider adding `--format json` in a future enhancement for machine-readable output
- Document the format change clearly in release notes

**Risk**: Sorting changes could surprise users expecting original insertion order
**Mitigation**:
- Sorting by status is intuitive and matches user expectations
- Document sorting behavior clearly
- Insertion order is preserved within each status group

**Risk**: UUID display makes output less human-readable
**Mitigation**:
- UUIDs are necessary for command reference (can't use names which may duplicate)
- UUID format is compact and standard
- Consider shortened display in future enhancement

## Alternatives Considered

1. **Keep current simple format, add separate `--details` flag**: Rejected because status visibility is essential and should always be shown
2. **Use custom IDs (sequential numbers)**: Rejected because they would be unstable across sessions and task deletions
3. **Show timestamps by default**: Rejected because it makes normal output too verbose; `--long` flag is optional
4. **Add color coding instead of ASCII symbols**: Rejected because ASCII symbols work in all terminal environments

## Implementation Notes

- Update `tasky_cli/commands/tasks.py` to format output with status indicators
- Update `TaskService.get_all_tasks()` consumers to handle new output format
- Add `--long/-l` option to `task list` command
- Ensure sorting happens in presentation layer (CLI), not service layer
- Use ISO 8601 format for timestamps: `YYYY-MM-DDTHH:MM:SSZ`

## Related Changes

- Builds on: `add-task-filtering` (compatible with status filtering)
- Complements: `task-timestamp-management` (displays created/updated times)
- Prep for: Future `--format json` or machine-readable output options
