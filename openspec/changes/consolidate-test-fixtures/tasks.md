# Tasks: Consolidate Test Fixtures

## Phase 1: Add Shared Fixture to conftest.py

### Task 1.1: Add initialized_project fixture to conftest.py
- Open `packages/tasky-cli/tests/conftest.py`
- Add import: `from pathlib import Path`
- Add import: `from tasky_cli.commands.projects import project_app`
- Add `initialized_project` fixture with implementation matching duplicated version
- Add comprehensive docstring explaining fixture purpose and behavior
- **Acceptance**: Fixture exists in conftest.py with proper type hints and docstring

### Task 1.2: Verify pytest discovers shared fixture
- Run `uv run pytest packages/tasky-cli/tests/ --collect-only` to verify fixture discovery
- Verify `initialized_project` appears in collected fixtures
- **Acceptance**: Pytest discovers initialized_project from conftest.py

## Phase 2: Remove Duplicates from Test Files

### Task 2.1: Remove duplicate from test_task_create.py
- Open `packages/tasky-cli/tests/test_task_create.py`
- Remove lines 12-25 (duplicate initialized_project fixture)
- Run `uv run pytest packages/tasky-cli/tests/test_task_create.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: test_task_create.py has no local initialized_project; all tests pass

### Task 2.2: Remove duplicate from test_task_show.py
- Open `packages/tasky-cli/tests/test_task_show.py`
- Remove lines 12-25 (duplicate initialized_project fixture)
- Run `uv run pytest packages/tasky-cli/tests/test_task_show.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: test_task_show.py has no local initialized_project; all tests pass

### Task 2.3: Remove duplicate from test_task_update.py
- Open `packages/tasky-cli/tests/test_task_update.py`
- Remove lines 14-27 (duplicate initialized_project fixture)
- Run `uv run pytest packages/tasky-cli/tests/test_task_update.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: test_task_update.py has no local initialized_project; all tests pass

### Task 2.4: Remove duplicate from test_task_list_format.py
- Open `packages/tasky-cli/tests/test_task_list_format.py`
- Remove lines 12-25 (duplicate initialized_project fixture)
- Run `uv run pytest packages/tasky-cli/tests/test_task_list_format.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: test_task_list_format.py has no local initialized_project; all tests pass

### Task 2.5: Remove duplicate from test_import_export.py
- Open `packages/tasky-cli/tests/test_import_export.py`
- Remove lines 19-32 (duplicate initialized_project fixture)
- Run `uv run pytest packages/tasky-cli/tests/test_import_export.py -v`
- Verify all tests pass with identical behavior
- **Acceptance**: test_import_export.py has no local initialized_project; all tests pass

## Phase 3: Final Validation

### Task 3.1: Run full test suite
- Run `uv run pytest packages/tasky-cli/tests/ -v`
- Verify all 577 tests pass
- Verify zero test failures or errors
- **Acceptance**: Complete test suite passes

### Task 3.2: Verify code quality checks
- Run `uv run ruff check --fix packages/tasky-cli/tests/`
- Run `uv run pyright packages/tasky-cli/tests/`
- Verify zero linting or type errors
- **Acceptance**: All quality checks pass

### Task 3.3: Verify coverage maintained
- Run `uv run pytest --cov=packages/tasky-cli --cov-report=term-missing`
- Verify coverage ≥80% threshold maintained
- **Acceptance**: Coverage threshold met

### Task 3.4: Verify duplication removed
- Run `grep -r "def initialized_project" packages/tasky-cli/tests/`
- Verify only one match (in conftest.py)
- **Acceptance**: Only conftest.py contains initialized_project fixture definition

## Phase 4: Documentation

### Task 4.1: Update conftest.py module docstring
- Update module docstring to document all shared fixtures
- Explain fixture discovery mechanism for future contributors
- **Acceptance**: conftest.py has comprehensive module documentation

### Task 4.2: Verify git diff shows expected changes
- Review git diff to confirm:
  - conftest.py: +15 lines (fixture added)
  - test_task_create.py: -13 lines (duplicate removed)
  - test_task_show.py: -13 lines (duplicate removed)
  - test_task_update.py: -13 lines (duplicate removed)
  - test_task_list_format.py: -13 lines (duplicate removed)
  - test_import_export.py: -13 lines (duplicate removed)
  - Net change: -50 lines (approximate)
- **Acceptance**: Git diff shows duplication removed; net negative line count
