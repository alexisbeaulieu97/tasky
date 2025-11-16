## 1. Design and Specification

- [ ] 1.1 Define `Validator` and `ValidationResult` protocols
- [ ] 1.2 Draft spec for `cli-input-validation` capability
- [ ] 1.3 Validate spec with `openspec validate add-cli-input-validators --strict`

## 2. Implementation

- [ ] 2.1 Create `packages/tasky-cli/src/tasky_cli/validators.py` module
- [ ] 2.2 Implement `ValidationResult[T]` dataclass
- [ ] 2.3 Implement `TaskIdValidator` (UUID format validation)
- [ ] 2.4 Implement `DateValidator` (ISO 8601 format validation)
- [ ] 2.5 Implement `StatusValidator` (valid status values)
- [ ] 2.6 Implement `PriorityValidator` (valid priority values)
- [ ] 2.7 Write unit tests for all validators (80%+ coverage)
- [ ] 2.8 Run `uv run pytest packages/tasky-cli/tests/test_validators.py`

## 3. CLI Integration

- [ ] 3.1 Update `show_command` to use `TaskIdValidator` before service invocation
- [ ] 3.2 Update `create_command` to validate task creation inputs
- [ ] 3.3 Update `update_command` to validate status/priority/due date
- [ ] 3.4 Update `list_command` to validate filter inputs
- [ ] 3.5 Update `delete_command` to validate task ID
- [ ] 3.6 Update `complete_command` to validate task ID
- [ ] 3.7 Run integration tests: `uv run pytest packages/tasky-cli/tests/ -k command`

## 4. Cleanup

- [ ] 4.1 Remove `_is_valid_date_format` helper from tasks.py
- [ ] 4.2 Remove `_validate_and_apply_update_fields` if fully subsumed
- [ ] 4.3 Ensure no duplicate validation logic remains

## 5. Validation

- [ ] 5.1 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [ ] 5.2 Run `uv run ruff check --fix`
- [ ] 5.3 Run `uv run pyright`
- [ ] 5.4 Manual CLI smoke test: `uv run tasky task create "my task"` and error cases
