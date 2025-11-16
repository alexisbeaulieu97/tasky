# Change: Consolidate Test Fixtures

## Why

The tasky-cli test suite has significant fixture duplication that violates the DRY (Don't Repeat Yourself) principle:

- **Duplicate code**: The `initialized_project` fixture is duplicated across 5 test files (test_task_create.py, test_task_show.py, test_task_update.py, test_import_export.py, test_task_list_format.py)
- **Identical implementation**: Each copy is 13 identical lines of code (65 lines total duplicated code)
- **Maintenance burden**: Changes to project initialization require updating 5 separate locations
- **Inconsistency risk**: Fixture implementations may drift apart over time if updated independently
- **Test fragility**: Similar issue exists with `runner` fixture pattern (though some files use the shared one in conftest.py)
- **Missed opportunity**: A `conftest.py` already exists for shared fixtures but is underutilized

This duplication creates unnecessary maintenance overhead and increases the risk of test inconsistencies. The project already has infrastructure for shared fixtures (`packages/tasky-cli/tests/conftest.py`) that should be leveraged.

## What Changes

Consolidate all duplicate test fixtures into the shared `conftest.py` module:

**Move to conftest.py**:
- `initialized_project(tmp_path, monkeypatch)` fixture → single shared implementation
- Verify all 5 test files can use the shared fixture with zero behavioral changes

**Optionally enhance fixture flexibility**:
- Add optional `backend` parameter to support testing with different storage backends
- Add optional `with_tasks` parameter to create pre-populated projects for common test scenarios

**Update test files**:
- Remove duplicate `initialized_project` fixture definitions from:
  - `test_task_create.py`
  - `test_task_show.py`
  - `test_task_update.py`
  - `test_import_export.py`
  - `test_task_list_format.py`
- All tests continue to use `initialized_project` fixture via pytest's fixture discovery

## Impact

- **Affected specs**: `test-fixtures` (new spec capturing shared fixture contracts)
- **Affected code**:
  - `packages/tasky-cli/tests/conftest.py` - add `initialized_project` fixture
  - 5 test files - remove duplicate fixture definitions
- **Backward compatibility**: Zero breaking changes (purely internal test refactoring)
- **Testing**: All existing 577 tests must continue to pass with zero modifications to test logic
- **Lines of code reduction**: ~52 lines removed (4 duplicates × 13 lines each)
- **Maintenance improvement**: Future project initialization changes only require one update location
