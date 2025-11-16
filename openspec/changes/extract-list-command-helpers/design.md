# Design: Extract Helper Functions from list_command

## Problem Analysis

### Current State

**list_command() complexity** (lines 132-323, 191 lines total):
```
Lines 199-237: Date validation for created_after (39 lines)
Lines 239-259: Date validation for created_before (DUPLICATE, 21 lines)
Lines 261-286: Filter construction logic (26 lines)
Lines 288-294: Empty result handling (7 lines)
Lines 296-323: Task rendering + summary (28 lines)
```

**Issues**:
1. **Duplication**: Date parsing appears twice with identical validation logic
2. **Mixed responsibilities**: Parsing, validation, business logic, rendering all in one function
3. **Complexity warnings**: C901, PLR0912 (too many branches), PLR0915 (too many statements)

### Why Only This Function?

tasks.py is 991 lines but **only list_command()** has complexity issues:
- create_command: Clean (no warnings)
- show_command: Clean
- update_command: Clean
- complete/cancel/reopen: Clean

**Conclusion**: File is well-organized. Only need targeted refactoring of this one function.

## Design Decision

### Option 1: Extract 3 Helper Functions (SELECTED)

**Benefit**: 3/5 (removes C901 warning, eliminates duplication)
**Cost**: 2/5 (extract functions, ~80 lines refactored)
**Score**: 1/5 (marginal yes)

Extract focused helpers:
1. `_parse_date_filter()` - Consolidate duplicate date parsing
2. `_build_task_list_filter()` - Isolate filter construction
3. `_render_task_list_summary()` - Isolate summary rendering

**Pros**:
- Removes C901 suppression
- Eliminates date parsing duplication
- Improves readability
- Low risk (function extraction)

**Cons**:
- Adds 3 new functions (more to navigate)
- Marginal benefit (only 1 function affected)

### Option 2: Split entire file into modules (REJECTED)

**Benefit**: 2/5 (aesthetic - file is large but well-organized)
**Cost**: 4/5 (4 new files, complex imports)
**Score**: -2/5 (strong no)

**Why rejected**: File has clear sections, only 1 complexity warning. Over-engineering.

### Option 3: Do nothing (CONSIDERED)

**Benefit**: 0/5
**Cost**: 0/5
**Score**: 0/5

Could just keep the noqa suppression. But since we can remove it with modest effort, might as well.

## Helper Function Designs

### Helper 1: _parse_date_filter()

**Purpose**: Consolidate duplicate date parsing logic

**Signature**:
```python
def _parse_date_filter(date_str: str, *, inclusive_end: bool = False) -> datetime:
    """Parse and validate date filter, returning timezone-aware datetime.

    Args:
        date_str: ISO 8601 date string (YYYY-MM-DD)
        inclusive_end: If True, adjust to end of day (23:59:59) for inclusive queries

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        typer.Exit: If date format is invalid
    """
```

**Implementation**:
```python
def _parse_date_filter(date_str: str, *, inclusive_end: bool = False) -> datetime:
    # Validate format
    if not _is_valid_date_format(date_str):
        typer.echo(
            f"Invalid date format: '{date_str}'. "
            "Expected ISO 8601 format: YYYY-MM-DD (e.g., 2025-01-01)",
            err=True,
        )
        raise typer.Exit(1)

    try:
        parsed_date = datetime.fromisoformat(date_str)

        # Adjust for inclusive end (created_before should include entire day)
        if inclusive_end:
            parsed_date = parsed_date + timedelta(days=1)

        # Ensure timezone-aware
        return parsed_date.replace(tzinfo=UTC)
    except ValueError:
        typer.echo(f"Invalid date: {date_str}", err=True)
        raise typer.Exit(1) from None
```

**Usage in list_command()**:
```python
# Before (39 lines + 21 lines = 60 lines):
if created_after is not None:
    if not _is_valid_date_format(created_after):
        typer.echo(...)
        raise typer.Exit(1)
    try:
        parsed_date = datetime.fromisoformat(created_after)
        created_after_dt = parsed_date.replace(tzinfo=UTC)
    except ValueError:
        ...

if created_before is not None:
    # ... duplicate logic ...

# After (4 lines):
created_after_dt = _parse_date_filter(created_after) if created_after else None
created_before_dt = _parse_date_filter(created_before, inclusive_end=True) if created_before else None
```

---

### Helper 2: _build_task_list_filter()

**Purpose**: Construct TaskFilter from validated inputs

**Signature**:
```python
def _build_task_list_filter(
    task_status: TaskStatus | None,
    created_after_dt: datetime | None,
    created_before_dt: datetime | None,
    search: str | None,
) -> tuple[TaskFilter | None, bool]:
    """Build task filter from validated inputs.

    Returns:
        Tuple of (filter_object, has_filters)
        - filter_object: TaskFilter if any filters active, None otherwise
        - has_filters: True if any filter criteria specified
    """
```

**Implementation**:
```python
def _build_task_list_filter(
    task_status: TaskStatus | None,
    created_after_dt: datetime | None,
    created_before_dt: datetime | None,
    search: str | None,
) -> tuple[TaskFilter | None, bool]:
    has_filters = (
        task_status is not None
        or created_after_dt is not None
        or created_before_dt is not None
        or search is not None
    )

    if not has_filters:
        return None, False

    task_filter = TaskFilter(
        statuses=[task_status] if task_status is not None else None,
        created_after=created_after_dt,
        created_before=created_before_dt,
        name_contains=search,
    )

    return task_filter, True
```

---

### Helper 3: _render_task_list_summary()

**Purpose**: Render "Showing X tasks" summary line

**Signature**:
```python
def _render_task_list_summary(tasks: list[TaskModel], has_filters: bool) -> None:
    """Render task list summary line with status breakdown.

    Args:
        tasks: List of tasks to summarize
        has_filters: Whether filters were applied (affects message)
    """
```

**Implementation**:
```python
def _render_task_list_summary(tasks: list[TaskModel], has_filters: bool) -> None:
    if not tasks:
        if has_filters:
            typer.echo("No matching tasks found")
        else:
            typer.echo("No tasks to display")
        return

    # Count by status
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)

    # Render summary
    task_word = "task" if len(tasks) == 1 else "tasks"
    typer.echo(
        f"\nShowing {len(tasks)} {task_word} "
        f"({pending} pending, {completed} completed, {cancelled} cancelled)"
    )
```

## Refactored list_command()

**After refactoring** (~80 lines, down from 191):
```python
@task_app.command(name="list")
@with_task_error_handling
def list_command(
    status: str | None = typer.Option(None, ...),
    created_after: str | None = typer.Option(None, ...),
    created_before: str | None = typer.Option(None, ...),
    search: str | None = typer.Option(None, ...),
    long: bool = typer.Option(False, ...),
) -> None:
    """List all tasks with status indicators and IDs."""

    # Validate status
    task_status = None
    if status is not None:
        valid_statuses = {s.value for s in TaskStatus}
        if status.lower() not in valid_statuses:
            valid_list = ", ".join(sorted(valid_statuses))
            typer.echo(f"Invalid status: '{status}'. Valid options: {valid_list}", err=True)
            raise typer.Exit(1)
        task_status = TaskStatus(status.lower())

    # Parse date filters
    created_after_dt = _parse_date_filter(created_after) if created_after else None
    created_before_dt = _parse_date_filter(created_before, inclusive_end=True) if created_before else None

    # Get service
    service = _get_service()

    # Normalize search
    if search and not search.strip():
        search = None

    # Build filter and fetch tasks
    task_filter, has_filters = _build_task_list_filter(
        task_status, created_after_dt, created_before_dt, search
    )

    tasks = service.find_tasks(task_filter) if task_filter else service.get_all_tasks()

    # Handle empty results
    if not tasks:
        _render_task_list_summary(tasks, has_filters)
        return

    # Sort and render tasks
    status_order = {TaskStatus.PENDING: 0, TaskStatus.COMPLETED: 1, TaskStatus.CANCELLED: 2}
    sorted_tasks = sorted(tasks, key=lambda t: status_order[t.status])

    for task in sorted_tasks:
        status_indicator = _get_status_indicator(task.status)
        typer.echo(f"{status_indicator} {task.task_id} {task.name} - {task.details}")

        if long:
            created = task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            updated = task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            typer.echo(f"  Created: {created} | Modified: {updated}")

    # Render summary
    _render_task_list_summary(tasks, has_filters)
```

## Migration Strategy

### Phase 1: Extract _parse_date_filter()
1. Add helper function with date parsing logic
2. Replace both date parsing blocks in list_command()
3. Run tests → verify behavioral equivalence

### Phase 2: Extract _build_task_list_filter()
1. Add helper function with filter construction
2. Replace filter building logic in list_command()
3. Run tests → verify equivalence

### Phase 3: Extract _render_task_list_summary()
1. Add helper function with summary rendering
2. Replace summary logic in list_command()
3. Run tests → verify equivalence

### Phase 4: Cleanup
1. Remove C901, PLR0912, PLR0915 suppressions from list_command()
2. Run `uv run ruff check` to verify no warnings
3. Run full test suite

## Testing Strategy

- All existing list_command tests must pass without modification
- Verify output format is identical (no changes to user-facing behavior)
- Test coverage maintained at ≥80%

## Success Criteria

✅ list_command() has no complexity suppressions
✅ Duplicate date parsing logic removed
✅ Function length reduced from 191 to ~80 lines
✅ All 577 tests pass
✅ Zero linting warnings for list_command()
✅ Behavioral equivalence maintained
