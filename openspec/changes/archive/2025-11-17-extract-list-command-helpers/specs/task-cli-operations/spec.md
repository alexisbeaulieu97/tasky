# Spec Delta: task-cli-operations

## ADDED Requirements

### Requirement: Task List Command Complexity Management

The task list command SHALL maintain reasonable cyclomatic complexity through focused helper functions to ensure maintainability and readability.

#### Helper Functions

The tasks.py module SHALL provide the following helpers for list_command:

- `_parse_date_filter(date_str: str, *, inclusive_end: bool) -> datetime`: Parse and validate ISO 8601 dates with timezone handling
- `_build_task_list_filter(...) -> tuple[TaskFilter | None, bool]`: Construct task filter from validated inputs
- `_render_task_list_summary(tasks, has_filters) -> None`: Render "Showing X tasks" summary line

**Complexity Constraints**:
- list_command() SHALL NOT have cyclomatic complexity >10 (no C901 suppression)
- Date parsing logic SHALL NOT be duplicated
- Each helper function SHALL have single, clear responsibility

#### Scenario: Date filter parsing consolidation

```gherkin
Given a user runs "tasky task list --created-after 2025-11-15"
When the validation helper parses the date filter
Then _parse_date_filter() is called with inclusive_end=False
And the returned datetime is timezone-aware UTC
And the time component is 00:00:00 (start of day)
And date validation happens in exactly one location (no duplication)
```

#### Scenario: Inclusive end-of-day handling

```gherkin
Given a user runs "tasky task list --created-before 2025-11-15"
When the validation helper parses the date filter
Then _parse_date_filter() is called with inclusive_end=True
And the returned datetime represents 2025-11-16 00:00:00 UTC
And the filter correctly includes all of 2025-11-15 (exclusive upper bound pattern)
```

#### Scenario: Task list summary rendering

```gherkin
Given a task list contains 5 tasks (2 pending, 2 completed, 1 cancelled)
When _render_task_list_summary() renders the summary
Then the output shows "Showing 5 tasks (2 pending, 2 completed, 1 cancelled)"
And the plural "tasks" is used (not "task")
```

```gherkin
Given a task list contains 1 task
When _render_task_list_summary() renders the summary
Then the output shows "Showing 1 task (...)"
And the singular "task" is used
```

#### Scenario: Empty results with filters

```gherkin
Given a user applies filters that match no tasks
When _render_task_list_summary() is called with empty list and has_filters=True
Then the output shows "No matching tasks found"
And no breakdown line is shown
```

```gherkin
Given a user lists tasks with no filters and project has no tasks
When _render_task_list_summary() is called with empty list and has_filters=False
Then the output shows "No tasks to display"
And no breakdown line is shown
```

---

## MODIFIED Requirements

None. This change is purely internal refactoring with no modifications to existing requirements.

---

## REMOVED Requirements

None. All existing requirements are preserved.
