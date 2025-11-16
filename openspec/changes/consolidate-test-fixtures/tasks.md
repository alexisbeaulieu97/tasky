# Tasks: Consolidate Test Fixtures

## 1. Add Shared Fixture to conftest.py

- [x] 1.1 Add `initialized_project` fixture to `packages/tasky-cli/tests/conftest.py`
- [x] 1.2 Add import: `from pathlib import Path`
- [x] 1.3 Add import: `from tasky_cli.commands.projects import project_app`
- [x] 1.4 Add comprehensive docstring explaining fixture purpose and behavior
- [x] 1.5 Run `uv run pytest packages/tasky-cli/tests/ --collect-only` to verify fixture discovery

## 2. Remove Duplicates from Test Files

- [x] 2.1 Remove duplicate from `test_task_create.py` (lines 12-25)
- [x] 2.2 Run `uv run pytest packages/tasky-cli/tests/test_task_create.py -v`
- [x] 2.3 Remove duplicate from `test_task_show.py` (lines 12-25)
- [x] 2.4 Run `uv run pytest packages/tasky-cli/tests/test_task_show.py -v`
- [x] 2.5 Remove duplicate from `test_task_update.py` (lines 14-27)
- [x] 2.6 Run `uv run pytest packages/tasky-cli/tests/test_task_update.py -v`
- [x] 2.7 Remove duplicate from `test_task_list_format.py` (lines 12-25)
- [x] 2.8 Run `uv run pytest packages/tasky-cli/tests/test_task_list_format.py -v`
- [x] 2.9 Remove duplicate from `test_import_export.py` (lines 19-32)
- [x] 2.10 Run `uv run pytest packages/tasky-cli/tests/test_import_export.py -v`

## 3. Final Validation

- [x] 3.1 Run full test suite: `uv run pytest packages/tasky-cli/tests/ -v`
- [x] 3.2 Verify all tests pass (zero failures)
- [x] 3.3 Run `uv run ruff check --fix packages/tasky-cli/tests/`
- [x] 3.4 Run `uv run pyright packages/tasky-cli/tests/`
- [x] 3.5 Run `uv run pytest --cov=packages/tasky-cli --cov-report=term-missing`
- [x] 3.6 Verify coverage ≥80% threshold maintained
- [x] 3.7 Run `grep -r "def initialized_project" packages/tasky-cli/tests/` and verify only one match

## 4. Documentation

- [x] 4.1 Update conftest.py module docstring to document all shared fixtures
- [x] 4.2 Verify git diff shows expected changes (~50 net lines removed)
