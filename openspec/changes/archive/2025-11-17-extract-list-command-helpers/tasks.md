# Tasks: Extract Helper Functions from list_command

## 1. Extract Date Parsing Helper

- [x] 1.1 Create `_parse_date_filter(date_str, *, inclusive_end)` helper function before list_command()
- [x] 1.2 Implement date format validation using existing `_is_valid_date_format()`
- [x] 1.3 Implement ISO 8601 parsing with timezone handling
- [x] 1.4 Implement inclusive_end logic (add timedelta(days=1) when True)
- [x] 1.5 Add comprehensive docstring with args, returns, raises
- [x] 1.6 Replace created_after parsing (lines 218-237) with `_parse_date_filter(created_after)`
- [x] 1.7 Replace created_before parsing (lines 239-259) with `_parse_date_filter(created_before, inclusive_end=True)`
- [x] 1.8 Run `uv run pytest packages/tasky-cli/tests/ -k "list" -v`

## 2. Extract Filter Construction Helper

- [x] 2.1 Create `_build_task_list_filter(...)` helper function before list_command()
- [x] 2.2 Accept parameters: task_status, created_after_dt, created_before_dt, search
- [x] 2.3 Return tuple: (TaskFilter | None, bool) for (filter_object, has_filters)
- [x] 2.4 Implement has_filters detection logic
- [x] 2.5 Implement TaskFilter construction
- [x] 2.6 Add comprehensive docstring
- [x] 2.7 Replace filter construction (lines 268-284) with call to `_build_task_list_filter()`
- [x] 2.8 Run `uv run pytest packages/tasky-cli/tests/ -k "list" -v`

## 3. Extract Summary Rendering Helper

- [x] 3.1 Create `_render_task_list_summary(tasks, has_filters)` helper function
- [x] 3.2 Implement empty result handling (different messages for filtered vs unfiltered)
- [x] 3.3 Implement status counting (pending, completed, cancelled)
- [x] 3.4 Implement singular/plural task word handling
- [x] 3.5 Implement summary line rendering
- [x] 3.6 Add comprehensive docstring
- [x] 3.7 Replace empty handling (lines 288-294) with call to `_render_task_list_summary()`
- [x] 3.8 Replace summary rendering (lines 318-323) with call to `_render_task_list_summary()`
- [x] 3.9 Run `uv run pytest packages/tasky-cli/tests/ -k "list" -v`

## 4. Cleanup and Validation

- [x] 4.1 Remove `# noqa: C901, PLR0912, PLR0915` from list_command() definition (line 132)
- [x] 4.2 Run `uv run ruff check packages/tasky-cli/src/tasky_cli/commands/tasks.py --select C901,PLR0912,PLR0915`
- [x] 4.3 Verify zero complexity warnings for list_command()
- [x] 4.4 Run full test suite: `uv run pytest packages/tasky-cli/tests/ -v`
- [x] 4.5 Run `uv run ruff check --fix packages/tasky-cli/`
- [x] 4.6 Run `uv run pyright packages/tasky-cli/`
- [x] 4.7 Run `uv run pytest --cov=packages/tasky-cli --cov-fail-under=80`
- [x] 4.8 Verify git diff shows expected line count reduction (~20 net lines removed)
