# Spec Delta: Task CLI Operations - Enhanced Task Listing

**Change**: `enhance-task-list-output`
**Spec**: `task-cli-operations`
**Status**: Draft

---

## ADDED Requirements

### Requirement: Task Listing Output Format

The `task list` command SHALL display tasks with status indicators, task IDs, and optional timestamps to provide users with essential task management information.

**Rationale**: Users need to see task status and IDs to effectively manage tasks and reference them in other commands. The enhanced output format provides critical context without requiring additional commands.

#### Scenario: List tasks displays status indicators and IDs

**Given** a project with 3 tasks in various statuses:
- Task 1: name="Buy milk", details="From the store", status=PENDING
- Task 2: name="Review PR", details="Code review", status=COMPLETED
- Task 3: name="Old project", details="Archived", status=CANCELLED

**When** the user runs `tasky task list`

**Then** the output SHALL display each task with format:
```
○ {task.id} {task.name} - {task.details}
✓ {task.id} {task.name} - {task.details}
✗ {task.id} {task.name} - {task.details}
```

**And** the status symbol SHALL map to task status:
- ○ (PENDING) for tasks with status = PENDING
- ✓ (COMPLETED) for tasks with status = COMPLETED
- ✗ (CANCELLED) for tasks with status = CANCELLED

**And** the task ID SHALL be displayed in UUID format (36 characters with hyphens)

**And** the output SHALL NOT include any additional formatting or colors beyond the required symbols

#### Scenario: List tasks are sorted by status

**Given** a project with tasks in mixed statuses (CANCELLED, PENDING, COMPLETED)

**When** the user runs `tasky task list`

**Then** the output SHALL display tasks in this order:
1. All PENDING tasks first
2. All COMPLETED tasks second
3. All CANCELLED tasks last

**And** within each status group, tasks SHALL appear in consistent order (preserving creation order or ID sort)

**And** the sorting SHALL apply regardless of the original insertion order

#### Scenario: List displays summary count

**Given** a project with:
- 5 PENDING tasks
- 3 COMPLETED tasks
- 2 CANCELLED tasks

**When** the user runs `tasky task list`

**Then** the output SHALL include a summary line after all tasks:
```
Showing 10 tasks (5 pending, 3 completed, 2 cancelled)
```

**And** the summary line SHALL use proper singular/plural forms:
- "1 task" if total is 1
- "X tasks" if total is not 1

**And** counts SHALL be accurate and match the displayed tasks

#### Scenario: List handles empty task list

**Given** a project with no tasks

**When** the user runs `tasky task list`

**Then** the output SHALL display:
```
No tasks to display
```

**And** no summary line SHALL be displayed

**And** the command SHALL exit with status code 0 (success)

#### Scenario: Long format displays timestamps

**Given** a project with a task created at "2025-11-12T10:30:00Z" and updated at "2025-11-12T14:45:30Z"

**When** the user runs `tasky task list --long`

**Then** each task line SHALL be followed by a timestamp line:
```
○ {task.id} {task.name} - {task.details}
  Created: 2025-11-12T10:30:00Z | Modified: 2025-11-12T14:45:30Z
```

**And** timestamps SHALL be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

**And** timestamp lines SHALL be indented by 2 spaces

**And** both `--long` and `-l` flags SHALL work identically

#### Scenario: Short form flag for long format

**Given** a project with tasks

**When** the user runs `tasky task list -l` (short form)

**Then** the behavior SHALL be identical to `tasky task list --long`

**And** timestamps SHALL be displayed for each task

#### Scenario: List works with status filtering

**Given** a project with 5 pending and 3 completed tasks

**When** the user runs `tasky task list --status pending`

**Then** the output SHALL display only pending tasks

**And** the summary line SHALL reflect filtered counts:
```
Showing 5 tasks (5 pending, 0 completed, 0 cancelled)
```

**And** tasks SHALL still be sorted and formatted with status indicators and IDs

**And** the summary line SHALL indicate that filtering was applied (context preserved from status filter)

#### Scenario: Help text documents output format

**Given** a user running the CLI

**When** the user runs `tasky task list --help`

**Then** the help text SHALL document:
- The output format (status indicator, ID, name, details)
- Status indicator symbols (○, ✓, ✗)
- The meaning of each status indicator
- The `--long` / `-l` flag and its effect
- Example output showing the enhanced format
- How the summary line is displayed

**And** the help text SHALL be clear and user-friendly

---

## Notes

### Implementation Details

- Status indicator display MUST be first element in each task line
- UUIDs MUST be displayed in full (no shortening)
- Output format is backwards-incompatible with previous simple format
- Sorting happens in presentation layer (CLI commands), not in service layer
- Timestamps require that `task.created_at` and `task.updated_at` fields exist
- Summary counts MUST be accurate even when combined with status filtering

### Related Requirements

- Builds on: "Task commands use service factory" (uses service to retrieve tasks)
- Builds on: "Transparent backend selection" (works with any configured backend)
- Compatible with: Task filtering (from add-task-filtering change)
- Requires: "Task timestamp management" spec (for created_at/updated_at fields)

### Output Examples

Basic format:
```
○ 550e8400-e29b-41d4-a716-446655440000 Buy milk - From the store
✓ 550e8400-e29b-41d4-a716-446655440001 Review PR - Code review
✗ 550e8400-e29b-41d4-a716-446655440002 Old project - Archived

Showing 3 tasks (1 pending, 1 completed, 1 cancelled)
```

Long format with timestamps:
```
○ 550e8400-e29b-41d4-a716-446655440000 Buy milk - From the store
  Created: 2025-11-12T10:30:00Z | Modified: 2025-11-12T10:30:00Z
✓ 550e8400-e29b-41d4-a716-446655440001 Review PR - Code review
  Created: 2025-11-11T14:20:00Z | Modified: 2025-11-12T09:15:00Z
✗ 550e8400-e29b-41d4-a716-446655440002 Old project - Archived
  Created: 2025-11-10T08:00:00Z | Modified: 2025-11-10T08:00:00Z

Showing 3 tasks (1 pending, 1 completed, 1 cancelled)
```

Filtered by status:
```
○ 550e8400-e29b-41d4-a716-446655440000 Buy milk - From the store

Showing 1 task (1 pending, 0 completed, 0 cancelled)
```

Empty list:
```
No tasks to display
```

---
