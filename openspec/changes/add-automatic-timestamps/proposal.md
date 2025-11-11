# Change: Automatic Timestamp Management

## Why

Tasks currently use timezone-naive timestamps and lack automatic update tracking. This change implements UTC-aware timestamps with explicit `mark_updated()` method to provide clear audit trails and track when tasks are modified.

## What Changes

- Update `TaskModel.created_at` to use `datetime.now(tz=UTC)` factory
- Update `TaskModel.updated_at` to use `datetime.now(tz=UTC)` factory  
- Add `TaskModel.mark_updated()` method to explicitly refresh `updated_at`
- Update `TaskService.update_task()` to call `task.mark_updated()` before saving
- Add comprehensive test suite for timestamp behavior
- Create `packages/tasky-tasks/tests/` directory with unit and integration tests

## Impact

- **Affected specs**: `task-timestamp-management` (new capability)
- **Affected code**: 
  - `packages/tasky-tasks/src/tasky_tasks/models.py` (modify `TaskModel`)
  - `packages/tasky-tasks/src/tasky_tasks/service.py` (modify `TaskService.update_task()`)
  - `packages/tasky-tasks/tests/` (new test files)
- **Backward compatibility**: Compatible - existing datetime fields remain, only adding timezone awareness
- **Dependencies**: None
