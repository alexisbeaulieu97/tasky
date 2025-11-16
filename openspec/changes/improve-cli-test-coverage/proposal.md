# Change: Improve CLI Test Coverage

## Why

The task CLI commands module has only 69% test coverage with 94 uncovered statements. Critical error handling paths (command failures, validation errors, import/export edge cases) are largely untested. This leaves user-facing features unvalidated and increases risk of poor error messages and unexpected behavior.

## What Changes

- Expand CLI task command tests to achieve ≥80% coverage
- Add comprehensive error handler tests for all exception types
- Add edge case tests for import/export strategies (empty files, malformed data, merge conflicts)
- Add tests for error message quality and formatting
- Ensure CLI error handling works correctly in all scenarios
- Add tests validating the new input validator layer (from Phase 7 CLI improvements)

## Impact

- **Affected specs**: `task-cli-operations`, `task-import-export-cli`
- **Affected code**: `packages/tasky-cli/tests/test_commands_tasks.py`
- **Backward compatibility**: Testing only; no API changes
- **User impact**: More reliable CLI with better error messages
