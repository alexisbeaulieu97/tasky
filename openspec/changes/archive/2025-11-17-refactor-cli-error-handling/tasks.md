## 1. Design and Specification

- [x] 1.1 Define `ErrorHandler` and `ErrorDispatcher` protocols
- [x] 1.2 Update `cli-error-presentation` spec delta for dispatcher pattern
- [x] 1.3 Validate spec with `openspec validate refactor-cli-error-handling --strict`

## 2. Implementation

- [x] 2.1 Create `packages/tasky-cli/src/tasky_cli/error_dispatcher.py` module
- [x] 2.2 Define `ErrorHandler` protocol: `handle(exc: Exception, verbose: bool) -> str`
- [x] 2.3 Define `ErrorDispatcher` class with registry pattern
- [x] 2.4 Extract `_handle_task_domain_error` to module
- [x] 2.5 Extract `_handle_storage_error` to module
- [x] 2.6 Extract `_handle_registry_error` to module
- [x] 2.7 Extract `_handle_project_not_found_error` to module
- [x] 2.8 Extract `_handle_generic_error` as fallback handler
- [x] 2.9 Implement registry registration for all handlers
- [x] 2.10 Write unit tests for dispatcher (80%+ coverage)
- [x] 2.11 Run `uv run pytest packages/tasky-cli/tests/test_error_dispatcher.py`

## 3. CLI Integration

- [x] 3.1 Update `with_task_error_handling` decorator to instantiate and use `ErrorDispatcher`
- [x] 3.2 Remove old `_handle_*` functions from tasks.py
- [x] 3.3 Remove `_dispatch_exception` helper from tasks.py
- [x] 3.4 Remove `_route_exception_to_handler` helper from tasks.py
- [x] 3.5 Simplify decorator: wrap function, catch exceptions, call dispatcher, exit

## 4. Testing

- [x] 4.1 Run `uv run pytest packages/tasky-cli/tests/ -k "error or exception"`
- [x] 4.2 Verify error messages unchanged: test each exception type
- [x] 4.3 Verify exit codes unchanged: all should be 1 or 2 as before

## 5. Validation

- [x] 5.1 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [x] 5.2 Run `uv run ruff check --fix`
- [x] 5.3 Run `uv run pyright`
- [x] 5.4 Manual CLI smoke test with error scenarios:
  - `tasky task show invalid-id` → should show error
  - `tasky task create` (no name) → should show error
  - `tasky task update` (invalid status) → should show error
