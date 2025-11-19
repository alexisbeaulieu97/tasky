# Tasks: Harden Hook System

- [ ] Implement strict validation in `tasky_hooks.loader` (check `callable`, inspect signatures)
- [ ] Add unit tests for invalid hook scenarios (non-callable, wrong signature)
- [ ] Add round-trip serialization tests for all event types in `test_events.py`
- [ ] Create `docs/HOOKS.md` with event schemas and examples
- [ ] Add concurrency safety tests for the dispatcher
- [ ] Verify all tests pass
