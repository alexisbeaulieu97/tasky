## 1. Design and Specification

- [x] 1.1 Define `Validator` and `ValidationResult` protocols
- [x] 1.2 Draft spec for `cli-input-validation` capability
- [x] 1.3 Validate spec with `openspec validate add-cli-input-validators --strict`

## 2. Implementation

- [x] 2.1 Create `packages/tasky-cli/src/tasky_cli/validators.py` module
- [x] 2.2 Implement `ValidationResult[T]` dataclass
- [x] 2.3 Implement `TaskIdValidator` (UUID format validation)
- [x] 2.4 Implement `DateValidator` (ISO 8601 format validation)
- [x] 2.5 Implement `StatusValidator` (valid status values)
- [x] 2.6 Implement `PriorityValidator` (valid priority values)
- [x] 2.7 Write unit tests for all validators (80%+ coverage)
- [x] 2.8 Run `uv run pytest packages/tasky-cli/tests/test_validators.py`

## 3. CLI Integration

- [x] 3.1 Update `show_command` to use `TaskIdValidator` before service invocation
- [x] 3.2 Update `create_command` to validate task creation inputs
- [x] 3.3 Update `update_command` to validate status/priority/due date
- [x] 3.4 Update `list_command` to validate filter inputs
- [x] 3.5 Update `delete_command` to validate task ID
- [x] 3.6 Update `complete_command` to validate task ID
- [x] 3.7 Run integration tests: `uv run pytest packages/tasky-cli/tests/ -k command`

## 4. Cleanup

- [x] 4.1 Remove `_is_valid_date_format` helper from tasks.py
- [x] 4.2 Remove `_validate_and_apply_update_fields` if fully subsumed
- [x] 4.3 Ensure no duplicate validation logic remains

## 5. Validation

- [x] 5.1 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [x] 5.2 Run `uv run ruff check --fix`
- [x] 5.3 Run `uv run pyright`
- [x] 5.4 Manual CLI smoke test: `uv run tasky task create "my task"` and error cases
