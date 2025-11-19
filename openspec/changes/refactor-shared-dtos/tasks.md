# Tasks: Refactor Shared DTOs

- [ ] Create `packages/tasky-contracts` structure (pyproject.toml, src, tests)
- [ ] Move `TaskStatus` enum to `tasky-contracts`
- [ ] Define `TaskSnapshot` Pydantic model in `tasky-contracts`
- [ ] Update `tasky-tasks` to depend on `tasky-contracts`
- [ ] Refactor `TaskModel` in `tasky-tasks` to use shared `TaskStatus`
- [ ] Implement `to_snapshot()` method on `TaskModel` returning shared `TaskSnapshot`
- [ ] Update `tasky-hooks` to depend on `tasky-contracts`
- [ ] Refactor `BaseEvent` and subclasses to use shared `TaskSnapshot`
- [ ] Update `tasky-cli` and other consumers to fix imports
- [ ] Verify all tests pass
