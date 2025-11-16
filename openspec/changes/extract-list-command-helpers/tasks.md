# Tasks: Extract Helper Functions from list_command

## Phase 1: Extract Date Parsing Helper

### Task 1.1: Create _parse_date_filter() helper function
- Add function before list_command() definition
- Implement date format validation using existing _is_valid_date_format()
- Implement ISO 8601 parsing with timezone handling
- Implement inclusive_end logic (add timedelta(days=1) when True)
- Add comprehensive docstring with args, returns, raises
- **Acceptance**: Function exists with proper implementation

### Task 1.2: Replace created_after parsing in list_command()
- Replace lines 218-237 with single call: `created_after_dt = _parse_date_filter(created_after) if created_after else None`
- Remove inline date validation and error handling
- **Acceptance**: created_after uses helper function

### Task 1.3: Replace created_before parsing in list_command()
- Replace lines 239-259 with single call: `created_before_dt = _parse_date_filter(created_before, inclusive_end=True) if created_before else None`
- Remove duplicate date validation logic
- **Acceptance**: created_before uses helper function with inclusive_end=True

### Task 1.4: Test date parsing changes
- Run `uv run pytest packages/tasky-cli/tests/test_task_list_format.py -v`
- Run `uv run pytest packages/tasky-cli/tests/ -k "list" -v`
- Verify all tests pass
- **Acceptance**: All list command tests pass; date filtering works identically

## Phase 2: Extract Filter Construction Helper

### Task 2.1: Create _build_task_list_filter() helper function
- Add function before list_command() definition
- Accept parameters: task_status, created_after_dt, created_before_dt, search
- Return tuple: (TaskFilter | None, bool) for (filter_object, has_filters)
- Implement has_filters detection logic
- Implement TaskFilter construction
- Add comprehensive docstring
- **Acceptance**: Function exists and returns proper tuple

### Task 2.2: Replace filter construction in list_command()
- Replace lines 268-284 with call to _build_task_list_filter()
- Update task fetching logic to use returned filter and has_filters
- **Acceptance**: Filter construction uses helper; tests pass

## Phase 3: Extract Summary Rendering Helper

### Task 3.1: Create _render_task_list_summary() helper function
- Add function after list_command() definition (with other rendering helpers)
- Accept parameters: tasks, has_filters
- Implement empty result handling (different messages for filtered vs unfiltered)
- Implement status counting (pending, completed, cancelled)
- Implement singular/plural task word handling
- Implement summary line rendering
- Add comprehensive docstring
- **Acceptance**: Function exists with proper rendering logic

### Task 3.2: Replace summary logic in list_command()
- Replace lines 288-294 (empty handling) and lines 318-323 (summary) with calls to _render_task_list_summary()
- Call once for empty results (early return)
- Call once after rendering tasks (end of function)
- **Acceptance**: Summary rendering uses helper; output format unchanged

## Phase 4: Cleanup and Validation

### Task 4.1: Remove complexity suppressions
- Remove `# noqa: C901, PLR0912, PLR0915` from list_command() definition (line 132)
- **Acceptance**: Suppressions removed

### Task 4.2: Verify no complexity warnings
- Run `uv run ruff check packages/tasky-cli/src/tasky_cli/commands/tasks.py --select C901,PLR0912,PLR0915`
- Verify zero warnings for list_command()
- **Acceptance**: No complexity warnings

### Task 4.3: Run full test suite
- Run `uv run pytest packages/tasky-cli/tests/ -v`
- Verify all 577 tests pass
- **Acceptance**: Complete test suite passes

### Task 4.4: Verify code quality
- Run `uv run ruff check --fix packages/tasky-cli/`
- Run `uv run pyright packages/tasky-cli/`
- **Acceptance**: Zero linting or type errors

### Task 4.5: Verify line count reduction
- Check git diff for tasks.py
- Verify function length reduced (~60 lines of duplication removed, ~40 lines of helpers added = net -20 lines)
- Verify list_command() is now ~80 lines (down from 191)
- **Acceptance**: Expected line count reduction achieved
