# Tasks: Pluggable Logging System

## Phase 1: Create Logging Package Infrastructure

1. [x] Create `packages/tasky-logging/` directory structure
2. [x] Create `packages/tasky-logging/pyproject.toml` with package metadata
3. [x] Create `packages/tasky-logging/README.md` with package documentation
4. [x] Create `packages/tasky-logging/src/tasky_logging/__init__.py` with exports
5. [x] Create `packages/tasky-logging/src/tasky_logging/py.typed` marker file
6. [x] Create `packages/tasky-logging/tests/__init__.py` for test package

## Phase 2: Implement Logging Abstraction

7. [x] Implement `Logger` Protocol in `packages/tasky-logging/src/tasky_logging/__init__.py`
8. [x] Implement `get_logger(name: str)` factory function using stdlib logging
9. [x] Create `packages/tasky-logging/src/tasky_logging/config.py` module
10. [x] Implement `configure_logging(verbosity: int, format_style: str)` function
11. [x] Add unit tests for `get_logger()` in `packages/tasky-logging/tests/test_logging.py`
12. [x] Add unit tests for `configure_logging()` with different verbosity levels

## Phase 3: Integrate Logging into Domain Layer

13. [x] Update `packages/tasky-tasks/pyproject.toml` to add `tasky-logging` dependency
14. [x] Import `get_logger` in `packages/tasky-tasks/src/tasky_tasks/service.py`
15. [x] Add module-level logger in `TaskService`
16. [x] Add INFO log to `TaskService.create_task()` method
17. [x] Add DEBUG log to `TaskService.get_task()` method
18. [x] Add INFO log to `TaskService.update_task()` method
19. [x] Add INFO log to `TaskService.delete_task()` method
20. [x] Add DEBUG log to `TaskService.get_all_tasks()` method

## Phase 4: Integrate Logging into Storage Layer

21. [x] Update `packages/tasky-storage/pyproject.toml` to add `tasky-logging` dependency
22. [x] Import `get_logger` in `packages/tasky-storage/src/tasky_storage/backends/json/repository.py`
23. [x] Add module-level logger in `JsonTaskRepository`
24. [x] Add DEBUG log to `JsonTaskRepository.save_task()` method
25. [x] Add DEBUG log to `JsonTaskRepository.get_task()` method
26. [x] Add DEBUG log to `JsonTaskRepository.get_all_tasks()` method
27. [x] Add DEBUG log to `JsonTaskRepository.delete_task()` method
28. [x] Add WARNING log to storage error conditions

## Phase 5: Add CLI Verbosity Control

29. [x] Update `packages/tasky-cli/pyproject.toml` to add `tasky-logging` dependency
30. [x] Import `configure_logging` in `packages/tasky-cli/src/tasky_cli/__init__.py`
31. [x] Add `@app.callback()` decorator to create main callback function
32. [x] Add `--verbose` option to callback with count support (`-v`, `-vv`)
33. [x] Call `configure_logging(verbosity=verbose)` in callback
34. [x] Update root `pyproject.toml` workspace dependencies to include `tasky-logging`

## Phase 6: Testing and Documentation

35. [x] Add integration test for CLI verbosity in `packages/tasky-cli/tests/`
36. [x] Verify logging output at different verbosity levels
37. [x] Test that logging works without explicit configuration (defaults)
38. [x] Update VISION.md examples with actual CLI logging commands
39. [x] Run `uv run pytest` to verify all tests pass
40. [x] Run `uv run ruff check --fix` to ensure code quality

## Validation

- [x] Run `openspec validate add-pluggable-logging --strict` and resolve all issues
- [x] Verify `uv run tasky -v task list` shows INFO logs
- [x] Verify `uv run tasky -vv task list` shows DEBUG logs
- [x] Verify `uv run tasky task list` shows no logs (WARNING+ only)
- [x] Verify logging can be imported and used independently in tests
