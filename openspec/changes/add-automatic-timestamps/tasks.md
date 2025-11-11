# Tasks: Automatic Timestamp Management

**Change ID**: `add-automatic-timestamps`

## Implementation Checklist

### 1. Update TaskModel with UTC Timestamps
- [ ] Import `UTC` from `datetime` module
- [ ] Change `created_at` field factory to use `lambda: datetime.now(tz=UTC)`
- [ ] Change `updated_at` field factory to use `lambda: datetime.now(tz=UTC)`
- [ ] Add `mark_updated()` method that sets `self.updated_at = datetime.now(tz=UTC)`
- [ ] Verify model can be instantiated with timezone-aware datetimes

**Validation**: Create a TaskModel instance and verify `created_at.tzinfo == UTC`

### 2. Update TaskService to Call mark_updated()
- [ ] Modify `update_task()` method to call `task.mark_updated()` before saving
- [ ] Ensure `mark_updated()` is called for any method that modifies task state

**Validation**: Call `service.update_task()` and verify `updated_at` has changed

### 3. Create Test Suite for Timestamps
- [ ] Create `packages/tasky-tasks/tests/` directory if not exists
- [ ] Create `packages/tasky-tasks/tests/__init__.py`
- [ ] Create `packages/tasky-tasks/tests/test_models.py`
- [ ] Add test: `test_task_creation_sets_utc_timestamps()` - Verify both timestamps are UTC-aware
- [ ] Add test: `test_created_and_updated_start_equal()` - Verify timestamps are equal at creation
- [ ] Add test: `test_mark_updated_changes_timestamp()` - Verify `mark_updated()` updates `updated_at`
- [ ] Add test: `test_mark_updated_preserves_created_at()` - Verify `created_at` doesn't change
- [ ] Add test: `test_timestamps_serializable()` - Verify model can be serialized/deserialized with timestamps

**Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_models.py -v`

### 4. Create Service Tests for Timestamp Behavior
- [ ] Create `packages/tasky-tasks/tests/test_service.py`
- [ ] Create in-memory fake repository for testing
- [ ] Add test: `test_create_task_sets_timestamps()` - Verify service creates tasks with proper timestamps
- [ ] Add test: `test_update_task_modifies_updated_at()` - Verify service updates `updated_at` when updating

**Validation**: Run `uv run pytest packages/tasky-tasks/tests/test_service.py -v`

### 5. Final Integration and Cleanup
- [ ] Run full test suite: `uv run pytest`
- [ ] Run linter: `uv run ruff check --fix`
- [ ] Run formatter: `uv run ruff format`
- [ ] Verify all existing tests still pass
- [ ] Manually test CLI: `uv run tasky task create "Test" "Details"` and verify timestamps in storage

**Validation**: All checks pass, no regressions

## Dependencies

- No external dependencies required
- Must complete tasks sequentially (tests depend on implementation)

## Estimated Time

- Task 1-2: 30 minutes (implementation)
- Task 3-4: 45 minutes (comprehensive tests)
- Task 5: 15 minutes (integration and cleanup)

**Total**: ~90 minutes

## Notes

- Keep tests focused and independent
- Use `time.sleep(0.01)` in tests when verifying timestamp changes
- Ensure all datetime comparisons account for timezone-aware objects
- Follow existing code style and naming conventions from the repository
