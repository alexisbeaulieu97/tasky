# Change: Extract Helper Functions from list_command

## Why

The `list_command()` function in tasks.py has a cyclomatic complexity warning (C901) due to its 191-line implementation with multiple nested conditionals for date parsing, filter construction, and output rendering.

**Evidence**:
- Single C901 warning in tasks.py (line 132)
- Function length: 191 lines (lines 132-323)
- Only function in entire tasks.py with complexity warning
- Duplicate date parsing logic for created_after/created_before (40 lines each)

**Problem**:
- C901 suppression required (`noqa: C901, PLR0912, PLR0915`)
- Date validation duplicated twice with identical logic
- Function does too many things (parse dates, build filters, fetch data, render, summarize)

## What Changes

Extract 3 focused helper functions from `list_command()` to eliminate complexity warning without restructuring entire file:

1. **`_parse_date_filter(date_str: str, *, inclusive_end: bool) -> datetime`**
   - Consolidates duplicate date parsing (created_after and created_before)
   - Validates ISO 8601 format
   - Handles timezone conversion to UTC
   - Handles inclusive_end for created_before queries
   - Reduces duplication by ~35 lines

2. **`_build_task_list_filter(...) -> tuple[TaskFilter | None, bool]`**
   - Constructs TaskFilter from validated inputs
   - Determines if filters are active
   - Returns (filter_object, has_filters) tuple
   - Isolates filter construction logic

3. **`_render_task_list_summary(tasks: list[TaskModel], has_filters: bool) -> None`**
   - Renders summary line ("Showing X tasks...")
   - Handles singular/plural task word
   - Shows breakdown by status
   - Isolates output formatting logic

**Result**:
- list_command() drops from 191 lines to ~80 lines
- Removes C901, PLR0912, PLR0915 suppressions
- Improves readability with clear helper names
- Zero breaking changes (behavioral equivalence)

## Impact

- **Affected specs**: task-cli-operations (update complexity requirements)
- **Affected code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` - extract 3 helpers, refactor list_command
  - Net ~10 line reduction (remove duplication, add helper functions)
- **Backward compatibility**: Zero breaking changes (internal refactoring only)
- **Testing**: All existing tests must pass without modification
- **Risk**: Low (function extraction is low-risk refactoring)
