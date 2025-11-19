# Tasks: Harden Hook System

1.  [ ] Implement strict validation in `tasky_hooks.loader` (check `callable`, inspect signatures)
2.  [ ] Add unit tests for invalid hook scenarios (non-callable, wrong signature)
3.  [ ] Add round-trip serialization tests for all event types in `test_events.py`
4.  [ ] Create `docs/HOOKS.md` with event schemas and examples
5.  [ ] Add concurrency safety tests for the dispatcher
6.  [ ] Verify all tests pass
