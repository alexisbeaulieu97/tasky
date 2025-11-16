# Design: Unify Projects Error Handling

## Problem Analysis

### Current State

**projects.py error handling patterns** (395 lines total):
- 8 commands with inline try/except blocks
- 3 patterns of error handling:
  1. **Generic catch-all**: `except Exception as exc` with `# noqa: BLE001`
  2. **Specific + catch-all**: `except ValueError as exc` then `except Exception as exc`
  3. **typer.Exit passthrough**: `except typer.Exit: raise` then catch others

**Example duplicated pattern** (appears in info, list, register, unregister, discover):
```python
try:
    registry_service = get_project_registry_service()
    # ... command logic ...
except typer.Exit:
    raise
except ValueError as exc:
    typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(code=1) from exc
except Exception as exc:
    typer.echo(f"Unexpected error: {exc}", err=True)
    raise typer.Exit(code=1) from exc
```

**Issues**:
- No verbose mode for debugging
- Inconsistent error message format ("Error:", "Unexpected error:")
- No contextual suggestions (e.g., "Run 'tasky project list' to see registered projects" appears inline, not centralized)
- Suppressed broad exception catching (`# noqa: BLE001`)
- No typed exception routing

### tasks.py Established Pattern

**Error handling infrastructure** (tasks.py lines 606-830):
- `Handler` protocol for type safety
- `with_task_error_handling` decorator wraps all commands
- `render_error(message, suggestion, *, verbose, exc)` for consistent output
- `dispatch_exception(exc, *, verbose)` routes to appropriate handler
- `route_exception_to_handler(exc, *, verbose)` determines handler based on type
- 11 specialized handlers with contextual suggestions

**Command pattern**:
```python
@task_app.command("show")
@with_task_error_handling
def show_command(task_id: str, verbose: bool = False) -> None:
    # Clean command logic, no error handling
    service, uuid = parse_task_id_and_get_service(task_id)
    task = service.get_task(uuid)
    # ... render task ...
```

## Design Decision: Adopt tasks.py Pattern

### Option 1: Keep Ad-Hoc Error Handling (REJECTED)
Continue with inline try/except blocks in each command.

**Pros**: No refactoring needed
**Cons**: Inconsistent with tasks.py; duplication; no verbose mode; pattern divergence

### Option 2: Create Shared Error Handling Module (DEFERRED)
Extract error handling into `tasky_cli.error_handling` shared by tasks and projects.

**Pros**: Ultimate DRY; single source of truth
**Cons**: Requires refactoring tasks.py too; higher initial complexity; can do later if beneficial

### Option 3: Adopt tasks.py Pattern in projects.py (SELECTED)
Replicate tasks.py error handling pattern within projects.py.

**Pros**:
- Consistent pattern across CLI commands
- Clean separation (project-specific handlers in project module)
- Proven pattern (already works in tasks.py)
- Can consolidate to shared module later if needed

**Cons**: Some duplication between tasks.py and projects.py (acceptable for now)

**Decision**: Option 3. Adopt tasks.py pattern within projects.py. Future change can extract to shared module if duplication becomes burden.

## Error Handler Design

### Error Handler Infrastructure

**Location**: `packages/tasky-cli/src/tasky_cli/commands/projects.py`

**Components to add**:

1. **Handler Protocol**:
```python
from typing import Protocol

class Handler(Protocol):
    """Protocol for exception handlers."""

    def __call__(self, exc: Exception, *, verbose: bool) -> None:
        """Handle an exception and exit."""
        ...
```

2. **render_error Function**:
```python
def _render_error(
    message: str,
    suggestion: str | None = None,
    *,
    verbose: bool = False,
    exc: Exception | None = None,
) -> None:
    """Render error message with optional suggestion and verbose details."""
    typer.echo(f"Error: {message}", err=True)
    if suggestion:
        typer.echo(f"Suggestion: {suggestion}", err=True)
    if verbose and exc:
        typer.echo("\nDetailed error:", err=True)
        typer.echo(traceback.format_exc(), err=True)
```

3. **Decorator**:
```python
def with_project_error_handling(func: Callable) -> Callable:
    """Decorator to handle exceptions in project commands."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except typer.Exit:
            raise
        except Exception as exc:
            # Get verbose flag from kwargs if present
            verbose = kwargs.get("verbose", False)
            _dispatch_exception(exc, verbose=verbose)

    return wrapper
```

4. **Exception Routing**:
```python
def _dispatch_exception(exc: Exception, *, verbose: bool) -> None:
    """Route exception to appropriate handler."""
    handler = _route_exception_to_handler(exc, verbose=verbose)
    handler(exc, verbose=verbose)

def _route_exception_to_handler(exc: Exception, *, verbose: bool) -> Handler:
    """Determine which handler to use for given exception."""
    # Import project-specific exceptions
    from tasky_projects.errors import ProjectNotFoundError
    from tasky_settings.errors import BackendNotRegisteredError
    from tasky_storage.errors import StorageError

    if isinstance(exc, ProjectNotFoundError):
        return _handle_project_not_found
    if isinstance(exc, BackendNotRegisteredError):
        return _handle_backend_not_registered
    if isinstance(exc, StorageError):
        return _handle_storage_error
    if isinstance(exc, (ValueError, TypeError)):
        return _handle_validation_error
    return _handle_generic_error
```

### Specialized Handlers

**Project-specific handlers**:

```python
def _handle_project_not_found(exc: Exception, *, verbose: bool) -> None:
    """Handle ProjectNotFoundError."""
    _render_error(
        str(exc),
        "Run 'tasky project list' to see all registered projects.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from None

def _handle_backend_not_registered(exc: Exception, *, verbose: bool) -> None:
    """Handle BackendNotRegisteredError."""
    from tasky_settings import registry
    available = ", ".join(registry.list_backends())
    _render_error(
        str(exc),
        f"Available backends: {available}",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from None

def _handle_storage_error(exc: Exception, *, verbose: bool) -> None:
    """Handle storage-related errors."""
    _render_error(
        f"Storage operation failed: {exc}",
        "Check file permissions and disk space.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(3) from None  # Exit code 3 for storage errors (matching tasks.py)

def _handle_validation_error(exc: Exception, *, verbose: bool) -> None:
    """Handle validation errors (ValueError, TypeError)."""
    _render_error(
        str(exc),
        None,  # Validation errors should have self-explanatory messages
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from None

def _handle_generic_error(exc: Exception, *, verbose: bool) -> None:
    """Handle unexpected errors."""
    _render_error(
        f"Unexpected error: {exc}",
        "Use --verbose for detailed error information.",
        verbose=verbose,
        exc=exc,
    )
    raise typer.Exit(1) from None
```

### Verbose Mode Integration

**Add verbose flag to commands**:
```python
@project_app.command("info")
@with_project_error_handling
def info_command(
    project_name: str | None = typer.Option(None, "--project-name", "-p", ...),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed error information"),
) -> None:
    """Display project configuration information."""
    # Clean command logic, no try/except
    ...
```

**Verbose mode behavior** (matching tasks.py):
- Non-verbose: User-friendly error message + suggestion
- Verbose: User-friendly message + suggestion + full stack trace

## Migration Strategy

### Phase 1: Add Error Handling Infrastructure
1. Add `Handler` protocol
2. Add `_render_error()` function
3. Add `_dispatch_exception()` and `_route_exception_to_handler()`
4. Add 5 specialized handlers
5. Add `with_project_error_handling` decorator
6. Verify module still loads

### Phase 2: Refactor Commands One at a Time
For each command (init, info, list, register, unregister, discover):
1. Add `@with_project_error_handling` decorator
2. Add `verbose: bool = typer.Option(False, "--verbose", "-v", ...)` parameter
3. Remove inline try/except blocks
4. Move command logic to top level
5. Run tests for that command
6. Verify error behavior unchanged (except verbose mode added)

**Order** (simplest to most complex):
1. `init_command` (simplest error handling)
2. `info_command`
3. `register_command`
4. `unregister_command`
5. `discover_command`
6. `list_command` (most complex, has clean flag logic)

### Phase 3: Remove `noqa` Suppressions
1. Remove all `# noqa: BLE001` from projects.py
2. Remove all `# noqa: C901` that are no longer needed
3. Run `uv run ruff check projects.py` to verify

### Phase 4: Add Error Handling Tests
1. Test verbose mode shows stack traces
2. Test non-verbose mode shows clean errors
3. Test each exception type routes to correct handler
4. Test exit codes are correct

## Testing Strategy

### Behavioral Equivalence Tests
- All existing project commands must continue to work
- Error messages may improve (more consistent, better suggestions)
- Exit codes must remain unchanged

### New Tests for Error Handling
```python
def test_verbose_mode_shows_stack_trace(runner):
    """Test that --verbose shows detailed error information."""
    result = runner.invoke(project_app, ["info", "--project-name", "nonexistent", "--verbose"])
    assert result.exit_code == 1
    assert "Detailed error:" in result.stdout

def test_backend_not_registered_error_shows_available_backends(runner):
    """Test that backend errors suggest available backends."""
    result = runner.invoke(project_app, ["init", "--backend", "invalid"])
    assert result.exit_code == 1
    assert "Available backends:" in result.stdout
    assert "json" in result.stdout
```

## Success Criteria

✅ `with_project_error_handling` decorator implemented
✅ 5 specialized error handlers implemented
✅ All 8 inline try/except blocks removed
✅ All `# noqa: BLE001` suppressions removed
✅ Verbose mode supported across all project commands
✅ All existing tests pass with zero modifications
✅ Error messages are consistent and helpful
✅ Exit codes match tasks.py pattern (1 for user errors, 3 for storage errors)
✅ Code quality improved (no broad exception catches)
