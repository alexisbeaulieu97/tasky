# Tasks: Refactor Shared DTOs

1.  [ ] Create `packages/tasky-contracts` structure (pyproject.toml, src, tests)
2.  [ ] Move `TaskStatus` enum to `tasky-contracts`
3.  [ ] Define `TaskSnapshot` Pydantic model in `tasky-contracts`
4.  [ ] Update `tasky-tasks` to depend on `tasky-contracts`
5.  [ ] Refactor `TaskModel` in `tasky-tasks` to use shared `TaskStatus`
6.  [ ] Implement `to_snapshot()` method on `TaskModel` returning shared `TaskSnapshot`
7.  [ ] Update `tasky-hooks` to depend on `tasky-contracts`
8.  [ ] Refactor `BaseEvent` and subclasses to use shared `TaskSnapshot`
9.  [ ] Update `tasky-cli` and other consumers to fix imports
10. [ ] Verify all tests pass
