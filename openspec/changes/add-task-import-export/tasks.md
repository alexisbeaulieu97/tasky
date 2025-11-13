# Implementation Tasks: Add Task Import/Export

This document outlines the ordered implementation tasks for adding task import/export functionality. Tasks are designed to deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: Domain Models and Schemas

- [ ] **Task 1.1**: Create export schema models
  - Create `packages/tasky-tasks/src/tasky_tasks/export.py`
  - Define `TaskSnapshot` Pydantic model
  - Define `ExportDocument` Pydantic model
  - Define `ImportResult` Pydantic model
  - Add docstrings and field descriptions
  - **Validation**: Models import and validate successfully

- [ ] **Task 1.2**: Create import/export exceptions
  - Update `packages/tasky-tasks/src/tasky_tasks/exceptions.py`
  - Add `ImportExportError` base exception
  - Add `ExportError` for export failures
  - Add `ImportError` for import failures
  - Add `InvalidExportFormatError` for malformed JSON
  - Add `IncompatibleVersionError` for version mismatch
  - Add `TaskValidationError` for invalid task data in import
  - **Validation**: Exceptions inherit correctly and compile

### Phase 2: Export Implementation

- [ ] **Task 2.1**: Implement `TaskImportExportService` export method
  - Create service class in `packages/tasky-tasks/src/tasky_tasks/export.py`
  - Implement `export_tasks(file_path: Path) -> ExportDocument`
  - Fetch all tasks via `TaskService.get_all_tasks()`
  - Convert each `TaskModel` to `TaskSnapshot`
  - Create `ExportDocument` with metadata
  - **Validation**: Method signature and documentation complete

- [ ] **Task 2.2**: Implement JSON serialization for export
  - Serialize `ExportDocument` to JSON
  - Use ISO 8601 format for timestamps
  - Write to file at specified path
  - Create parent directory if needed
  - Include proper error handling for I/O errors
  - **Validation**: Export file is valid JSON

- [ ] **Task 2.3**: Write unit tests for export
  - Create `packages/tasky-tasks/tests/test_export.py`
  - Test export creates valid JSON
  - Test all task fields are preserved
  - Test metadata (version, timestamp, task_count) is correct
  - Test empty task list handled
  - Test timestamp formatting is ISO 8601
  - **Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_export.py -v`

- [ ] **Task 2.4**: Add export CLI command
  - Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add `export_command(file_path: str)` function
  - Accept file path as argument
  - Create service and call export
  - Show success message with file path and task count
  - Handle errors gracefully with user-friendly messages
  - **Validation**: Run `uv run tasky task export test.json` and verify file created

### Phase 3: Import Implementation

- [ ] **Task 3.1**: Implement append strategy
  - Create `_apply_append_strategy()` method in `TaskImportExportService`
  - Add imported tasks without modification
  - Re-key duplicate task IDs with new UUID
  - Return `ImportResult` with created count
  - **Validation**: Method compiles and logic correct

- [ ] **Task 3.2**: Implement replace strategy
  - Create `_apply_replace_strategy()` method
  - Delete all existing tasks first
  - Import all tasks from file
  - Return `ImportResult` with created count
  - **Validation**: Method compiles and logic correct

- [ ] **Task 3.3**: Implement merge strategy
  - Create `_apply_merge_strategy()` method
  - Check each imported task ID against existing
  - Update existing tasks by ID
  - Create new tasks with new IDs
  - Return `ImportResult` with created and updated counts
  - **Validation**: Method compiles and logic correct

- [ ] **Task 3.4**: Implement import validation
  - Create `_load_and_validate(file_path: Path)` method
  - Parse JSON file
  - Validate against `ExportDocument` schema
  - Check version compatibility (reject if version > 1.0)
  - Convert each `TaskSnapshot` to `TaskModel`
  - Raise appropriate exceptions for errors
  - **Validation**: Invalid files raise correct exceptions

- [ ] **Task 3.5**: Implement dry-run support
  - Add `dry_run: bool` parameter to `import_tasks()`
  - When dry_run=True, simulate strategy without saving
  - Return preview of what would happen
  - **Validation**: Dry-run shows accurate preview

- [ ] **Task 3.6**: Write unit tests for import strategies
  - Create `packages/tasky-tasks/tests/test_import.py`
  - Test append strategy with new and duplicate IDs
  - Test replace strategy clears all first
  - Test merge strategy updates by ID
  - Test each strategy produces correct `ImportResult`
  - Test dry-run doesn't modify data
  - **Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_import.py -v`

- [ ] **Task 3.7**: Write integration tests for import validation
  - Test valid export file imports successfully
  - Test invalid JSON rejected
  - Test missing required fields rejected
  - Test version mismatch rejected
  - Test task data validation
  - Test helpful error messages
  - **Validation**: Integration tests pass

- [ ] **Task 3.8**: Add import CLI command
  - Update `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
  - Add `import_command(file_path: str, strategy: str, dry_run: bool)`
  - Accept file path as argument
  - Accept `--strategy` option (append, replace, merge)
  - Accept `--dry-run` flag
  - Validate strategy value
  - Create service and call import
  - Show result summary (created, updated, skipped)
  - Handle errors with user-friendly messages
  - **Validation**: Run `uv run tasky task import test.json --strategy append`

### Phase 4: Integration and End-to-End Testing

- [ ] **Task 4.1**: Write end-to-end CLI tests
  - Create `packages/tasky-cli/tests/test_import_export.py`
  - Test export → import → verify all data preserved
  - Test all three strategies
  - Test dry-run flag
  - Test error handling for invalid files
  - Test large task counts
  - **Validation**: Run `uv run pytest packages/tasky-cli/tests/test_import_export.py -v`

- [ ] **Task 4.2**: Manual smoke testing
  - Create fresh project: `uv run tasky project init`
  - Create tasks with various statuses
  - Export to JSON: `uv run tasky task export backup.json`
  - Verify JSON is valid and readable
  - Import with append: `uv run tasky task import backup.json --strategy append`
  - Verify task count doubled
  - Import with merge: same tasks, verify no duplicates
  - Import with replace: verify old tasks gone, new ones present
  - **Validation**: All operations work as expected

- [ ] **Task 4.3**: Performance testing
  - Create 1000+ task export
  - Measure export time (should be <1 second)
  - Measure import time (should be <1 second)
  - Verify memory usage is reasonable
  - **Validation**: Operations complete quickly

### Phase 5: Polish and Documentation

- [ ] **Task 5.1**: Update help text and documentation
  - Add examples to `tasky task export --help`
  - Add examples to `tasky task import --help`
  - Document all strategy options
  - Include example JSON structure
  - Document version compatibility
  - **Validation**: Help text is clear and useful

- [ ] **Task 5.2**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage meets ≥80% target
  - **Validation**: All tests pass with good coverage

- [ ] **Task 5.3**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors or warnings
  - **Validation**: Code passes all quality checks

- [ ] **Task 5.4**: Update project documentation
  - Add import/export section to README (if exists)
  - Document the three strategies
  - Include backup/restore examples
  - Note format stability promise
  - **Validation**: Documentation is complete and accurate

## Notes

- **Dependencies**: Tasks within each phase should be mostly sequential; some parallelization possible between phases
- **Testing**: Each phase includes unit tests; end-to-end tests in Phase 4
- **Validation**: Each task includes specific validation steps
- **Rollback**: Each task is independently reversible if issues arise

## Estimated Duration

- Phase 1: 30 minutes (models and schemas)
- Phase 2: 45 minutes (export implementation)
- Phase 3: 90 minutes (import implementation and strategies)
- Phase 4: 45 minutes (integration and testing)
- Phase 5: 30 minutes (polish and documentation)

**Total**: ~4 hours

## Success Criteria

- All tasks completed
- All tests passing (≥80% coverage)
- All validation steps confirmed
- Manual smoke testing successful
- Code quality checks passing
- User can export and import tasks with all three strategies
- Error messages are helpful and actionable
