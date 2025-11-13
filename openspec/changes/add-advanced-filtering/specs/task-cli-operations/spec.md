# Delta Spec: Advanced Task Filtering in task-cli-operations

## ADDED Requirements

### Requirement: Date Range Filtering on Task Creation Timestamp

The system SHALL support filtering tasks by creation date using `--created-after` and `--created-before` options.

**Rationale**: Users need to focus on recently created tasks or find tasks from specific time periods without manually inspecting timestamps. Date filtering is essential for time-based task organization.

#### Scenario: Filter tasks created after a specific date

**WHEN** the user runs `tasky task list --created-after 2025-01-01`
**THEN** the CLI SHALL display only tasks where `task.created_at >= 2025-01-01T00:00:00Z`
**AND** tasks created before 2025-01-01 SHALL NOT be displayed
**AND** the output format SHALL match existing task list format

#### Scenario: Filter tasks created before a specific date

**WHEN** the user runs `tasky task list --created-before 2025-12-31`
**THEN** the CLI SHALL display only tasks where `task.created_at <= 2025-12-31T23:59:59Z`
**AND** tasks created after 2025-12-31 SHALL NOT be displayed
**AND** the output format SHALL match existing task list format

#### Scenario: Filter tasks within a date range

**WHEN** the user runs `tasky task list --created-after 2025-11-01 --created-before 2025-11-30`
**THEN** the CLI SHALL display only tasks created between 2025-11-01 and 2025-11-30 inclusive
**AND** the filter SHALL use AND logic (both date conditions must match)
**AND** only tasks satisfying both date constraints SHALL appear

#### Scenario: Accept ISO 8601 date format

**WHEN** the user provides dates in ISO 8601 format (YYYY-MM-DD)
**THEN** the system SHALL parse dates correctly
**AND** dates SHALL be interpreted as UTC midnight (00:00:00Z)
**AND** the parsing SHALL NOT fail

#### Scenario: Reject invalid date format with helpful error

**WHEN** the user runs `tasky task list --created-after "Jan 1"` or `--created-after "2025/01/01"`
**THEN** the CLI SHALL display an error message
**AND** the error message SHALL include the expected format "YYYY-MM-DD"
**AND** the error message SHALL include an example like "2025-01-01"
**AND** the CLI SHALL exit with error status code 1
**AND** the CLI SHALL NOT call the task service

---

### Requirement: Text Search in Task Name and Details

The system SHALL support searching tasks by text matching in task name and details fields.

**Rationale**: Users need to find tasks mentioning specific keywords, problem descriptions, or project names without reading every task. Full-text search improves task discovery and navigation.

#### Scenario: Search tasks by text in name

**WHEN** the user runs `tasky task list --search "bug fix"`
**THEN** the CLI SHALL display tasks where "bug fix" appears in the task name
**AND** the search SHALL be case-insensitive
**AND** tasks not containing the search text SHALL NOT be displayed

#### Scenario: Search tasks by text in details

**WHEN** the user runs `tasky task list --search "urgent"`
**THEN** the CLI SHALL display tasks where "urgent" appears in either name or details fields
**AND** all matching fields SHALL be found (OR logic within name+details, AND with other criteria)

#### Scenario: Text search is case-insensitive

**WHEN** the user runs `tasky task list --search "Bug FIX"` or `--search "BUG FIX"`
**THEN** the CLI SHALL match tasks containing "bug fix", "Bug Fix", "BUG FIX", or any case variant
**AND** case sensitivity SHALL NOT affect results

#### Scenario: Text search is substring-based

**WHEN** the user runs `tasky task list --search "bug"`
**THEN** the CLI SHALL match tasks containing "bug", "Bug", "bugfix", "debugging", or any word containing "bug"
**AND** exact word matching SHALL NOT be required
**AND** partial matches SHALL be found

#### Scenario: Empty search text returns all tasks

**WHEN** the user provides `--search ""` (empty string)
**THEN** the CLI SHALL treat it as no search filter
**AND** all tasks SHALL be displayed (unless other filters are applied)

---

### Requirement: Combining Multiple Filter Criteria with AND Logic

The system SHALL support combining multiple filter criteria, with all criteria required to match (AND logic).

**Rationale**: Complex filtering scenarios require combining multiple dimensions (status, date, content). AND logic is intuitive—users expect to narrow results by adding more constraints.

#### Scenario: Filter by status AND date range

**WHEN** the user runs `tasky task list --status pending --created-after 2025-11-01`
**THEN** the CLI SHALL display only tasks that satisfy BOTH conditions:
  - status == TaskStatus.PENDING AND
  - created_at >= 2025-11-01T00:00:00Z
**AND** tasks that are pending but created before 2025-11-01 SHALL NOT appear
**AND** tasks created after 2025-11-01 but not pending SHALL NOT appear

#### Scenario: Filter by status AND search text

**WHEN** the user runs `tasky task list --status pending --search "urgent"`
**THEN** the CLI SHALL display only tasks matching BOTH:
  - status == TaskStatus.PENDING AND
  - name or details contain "urgent" (case-insensitive)
**AND** pending tasks not mentioning "urgent" SHALL NOT appear
**AND** tasks mentioning "urgent" that are not pending SHALL NOT appear

#### Scenario: Filter by date range AND search text

**WHEN** the user runs `tasky task list --created-after 2025-11-01 --created-before 2025-11-30 --search "bug"`
**THEN** the CLI SHALL display only tasks matching ALL three conditions:
  - created_at >= 2025-11-01T00:00:00Z AND
  - created_at <= 2025-11-30T23:59:59Z AND
  - name or details contain "bug"
**AND** the filter SHALL require all conditions to match

#### Scenario: Combine status, date range, AND search text

**WHEN** the user runs `tasky task list --status pending --created-after 2025-11-01 --search "fix"`
**THEN** the CLI SHALL display only tasks matching ALL criteria:
  - status == TaskStatus.PENDING AND
  - created_at >= 2025-11-01T00:00:00Z AND
  - name or details contain "fix"
**AND** each criterion reduces the result set (all must be satisfied)

---

### Requirement: Helpful Error Messages for Invalid Filtering Input

The system SHALL provide clear, actionable error messages when filter criteria are invalid.

**Rationale**: Users will occasionally provide malformed input (wrong date format, invalid status). Clear errors guide toward correct usage and reduce frustration.

#### Scenario: Invalid date format shows expected format

**WHEN** the user runs `tasky task list --created-after "2025-01-01T12:00:00"`
**THEN** the CLI SHALL reject the time component (not supported)
**AND** display an error: "Invalid date format: ... Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)"
**AND** the CLI SHALL exit with status code 1

#### Scenario: Future dates are accepted

**WHEN** the user runs `tasky task list --created-after 2099-12-31`
**THEN** the CLI SHALL accept the date
**AND** no tasks SHALL match (unless created in the far future)
**AND** the CLI SHALL display "No matching tasks found" (not an error)

#### Scenario: Empty result is distinguished from error

**WHEN** filtering produces zero matching tasks
**THEN** the CLI SHALL display "No matching tasks found" (informational)
**AND** the CLI SHALL exit with status code 0 (success)
**AND** the message SHALL differ from error messages

---

## MODIFIED Requirements

### Requirement: Task List Command Maintains Consistent Output Format

The `task list` command output format MUST remain consistent whether displaying filtered or unfiltered tasks, and MUST support AND-logic combination of multiple filter criteria.

**Original Behavior**: List command displays all tasks or filtered-by-status tasks with basic formatting.

**Modified Behavior**: List command displays filtered tasks (by status, date, or search) while maintaining consistent formatting and supporting AND-logic combination of criteria.

**Rationale**: Users expect consistent output formatting regardless of which filters are applied, and multiple independent filters must work together predictably using AND logic (all criteria must match).

#### Scenario: Filtered output matches existing format

**WHEN** the user applies any combination of filters
**THEN** the output format SHALL remain identical to the status-only filtering format
**AND** each task SHALL display the same fields in the same order
**AND** no additional metadata SHALL be added without explicit design

#### Scenario: Backward compatibility maintained

**WHEN** users run existing commands without new filter options
**THEN** behavior SHALL be identical to current implementation
**AND** `tasky task list --status pending` SHALL work unchanged
**AND** `tasky task list` with no filters SHALL show all tasks unchanged

#### Scenario: Multiple filters combine using AND logic

**WHEN** the user applies multiple filter options
**THEN** the system SHALL require all filter criteria to match (AND logic)
**AND** tasks that satisfy only some criteria SHALL NOT be displayed
**AND** only tasks matching every specified criterion SHALL appear

---

## Related Capabilities

This change extends `task-cli-operations` to support the advanced filtering layer built on top of status filtering. It complements the existing:
- Status filtering (already implemented via `--status`)
- Error handling patterns (applied to date validation)
- Output formatting conventions (preserved for consistency)

The implementation introduces `TaskFilter` model (defined in `tasky-tasks` domain), which encapsulates all filter criteria and the AND-logic matching algorithm.
