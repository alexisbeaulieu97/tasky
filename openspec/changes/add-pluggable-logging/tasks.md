# Tasks: Pluggable Logging System

## Phase 1: Create Logging Package Infrastructure

1. [ ] Create `packages/tasky-logging/` directory structure
2. [ ] Create `packages/tasky-logging/pyproject.toml` with package metadata
3. [ ] Create `packages/tasky-logging/README.md` with package documentation
4. [ ] Create `packages/tasky-logging/src/tasky_logging/__init__.py` with exports
5. [ ] Create `packages/tasky-logging/src/tasky_logging/py.typed` marker file
6. [ ] Create `packages/tasky-logging/tests/__init__.py` for test package

## Phase 2: Implement Logging Abstraction

7. [ ] Implement `Logger` Protocol in `packages/tasky-logging/src/tasky_logging/__init__.py`
8. [ ] Implement `get_logger(name: str)` factory function using stdlib logging
9. [ ] Create `packages/tasky-logging/src/tasky_logging/config.py` module
10. [ ] Implement `configure_logging(verbosity: int, format_style: str)` function
11. [ ] Add unit tests for `get_logger()` in `packages/tasky-logging/tests/test_logging.py`
12. [ ] Add unit tests for `configure_logging()` with different verbosity levels

## Phase 3: Integrate Logging into Domain Layer

13. [ ] Update `packages/tasky-tasks/pyproject.toml` to add `tasky-logging` dependency
14. [ ] Import `get_logger` in `packages/tasky-tasks/src/tasky_tasks/service.py`
15. [ ] Add module-level logger in `TaskService`
16. [ ] Add INFO log to `TaskService.create_task()` method
17. [ ] Add DEBUG log to `TaskService.get_task()` method
18. [ ] Add INFO log to `TaskService.update_task()` method
19. [ ] Add INFO log to `TaskService.delete_task()` method
20. [ ] Add DEBUG log to `TaskService.get_all_tasks()` method

## Phase 4: Integrate Logging into Storage Layer

21. [ ] Update `packages/tasky-storage/pyproject.toml` to add `tasky-logging` dependency
22. [ ] Import `get_logger` in `packages/tasky-storage/src/tasky_storage/backends/json/repository.py`
23. [ ] Add module-level logger in `JsonTaskRepository`
24. [ ] Add DEBUG log to `JsonTaskRepository.save_task()` method
25. [ ] Add DEBUG log to `JsonTaskRepository.get_task()` method
26. [ ] Add DEBUG log to `JsonTaskRepository.get_all_tasks()` method
27. [ ] Add DEBUG log to `JsonTaskRepository.delete_task()` method
28. [ ] Add WARNING log to storage error conditions

## Phase 5: Add CLI Verbosity Control

29. [ ] Update `packages/tasky-cli/pyproject.toml` to add `tasky-logging` dependency
30. [ ] Import `configure_logging` in `packages/tasky-cli/src/tasky_cli/__init__.py`
31. [ ] Add `@app.callback()` decorator to create main callback function
32. [ ] Add `--verbose` option to callback with count support (`-v`, `-vv`)
33. [ ] Call `configure_logging(verbosity=verbose)` in callback
34. [ ] Update root `pyproject.toml` workspace dependencies to include `tasky-logging`

## Phase 6: Testing and Documentation

35. [ ] Add integration test for CLI verbosity in `packages/tasky-cli/tests/`
36. [ ] Verify logging output at different verbosity levels
37. [ ] Test that logging works without explicit configuration (defaults)
38. [ ] Update VISION.md examples with actual CLI logging commands
39. [ ] Run `uv run pytest` to verify all tests pass
40. [ ] Run `uv run ruff check --fix` to ensure code quality

## Validation

- [ ] Run `openspec validate add-pluggable-logging --strict` and resolve all issues
- [ ] Verify `uv run tasky -v task list` shows INFO logs
- [ ] Verify `uv run tasky -vv task list` shows DEBUG logs
- [ ] Verify `uv run tasky task list` shows no logs (WARNING+ only)
- [ ] Verify logging can be imported and used independently in tests
