# task-filtering-cli Specification

## Purpose
TBD - created by archiving change add-task-filtering. Update Purpose after archive.
## Requirements
### Requirement: Task List Command Accepts Status Filter Option

The `task list` command MUST accept an optional status parameter to filter displayed tasks.

**Rationale**: Enables users to focus on relevant tasks without viewing the entire task list, improving usability for projects with many tasks.

#### Scenario: List tasks with status filter

**Given** a project with tasks in various statuses  
**When** the user runs `tasky task list --status pending`  
**Then** the CLI MUST display only tasks with `status == TaskStatus.PENDING`  
**And** the output format MUST match the existing task list format  
**And** no tasks with other statuses MUST appear in the output

#### Scenario: Support short form status option

**Given** a project with tasks  
**When** the user runs `tasky task list -s completed`  
**Then** the CLI MUST behave identically to `tasky task list --status completed`  
**And** only completed tasks MUST be displayed

#### Scenario: List all tasks when status not specified

**Given** a project with tasks  
**When** the user runs `tasky task list` (without --status)  
**Then** the CLI MUST display all tasks regardless of status  
**And** the behavior MUST be identical to the current implementation  
**And** backward compatibility MUST be preserved

---

### Requirement: CLI Validates Status Parameter

The CLI MUST validate the status parameter value and provide helpful error messages for invalid input.

**Rationale**: Prevents confusing errors and guides users toward correct usage, improving user experience.

#### Scenario: Reject invalid status values

**Given** the user runs `tasky task list --status invalid`  
**When** the CLI validates the status parameter  
**Then** the CLI MUST display an error message  
**And** the error message MUST list valid status values: "pending", "completed", "cancelled"  
**And** the CLI MUST exit with a non-zero status code  
**And** the CLI MUST NOT call the task service

#### Scenario: Accept valid status values case-insensitively

**Given** the user runs `tasky task list --status PENDING`  
**When** the CLI processes the status parameter  
**Then** the CLI MUST normalize the value to lowercase  
**And** the CLI MUST call the service with `TaskStatus.PENDING`  
**And** pending tasks MUST be displayed correctly

#### Scenario: Provide helpful usage examples

**Given** the user runs `tasky task list --help`  
**When** the help text is displayed  
**Then** the `--status` option MUST be documented  
**And** the help text MUST list valid values: "pending", "completed", "cancelled"  
**And** the help text MUST include usage examples  
**And** the short form `-s` MUST be documented

---

### Requirement: CLI Handles Empty Filter Results Gracefully

The CLI MUST provide clear feedback when filtering returns no tasks.

**Rationale**: Users should understand whether the filter worked correctly or if there are genuinely no matching tasks.

#### Scenario: Display message when filter returns no results

**Given** a project with only completed tasks  
**When** the user runs `tasky task list --status pending`  
**Then** the CLI MUST display a message indicating no pending tasks were found  
**And** the message MUST distinguish between "no tasks match filter" and "no tasks exist"  
**And** the CLI MUST exit with status code 0 (success)

#### Scenario: Display message when repository is empty

**Given** a project with no tasks  
**When** the user runs `tasky task list --status pending`  
**Then** the CLI MUST display a message indicating no tasks exist  
**And** the CLI MUST exit with status code 0 (success)

### Requirement: Task List Command Maintains Consistent Output Format

The `task list` command output format MUST remain consistent whether displaying all tasks or filtered tasks.

#### Scenario: Filtered output matches existing format

**Given** existing task list output shows "TaskName - TaskDetails"  
**When** the user filters by status  
**Then** filtered tasks MUST use the same output format  
**And** no additional status indicators MUST be added (unless explicitly designed)  
**And** the ordering of tasks MUST remain consistent

---

