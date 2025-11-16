# Change: Unify Projects Error Handling

## Why

The `projects.py` CLI module has inconsistent and ad-hoc error handling that diverges significantly from the sophisticated error handling pattern established in `tasks.py`:

**Current state of projects.py**:
- **8 duplicate try/except blocks** across commands (info, list, register, unregister, discover)
- **No error dispatcher**: Each command handles errors inline with similar but slightly different patterns
- **No verbose mode support**: Users cannot get detailed stack traces for debugging
- **Generic exception handling**: Most blocks catch broad `Exception` with `# noqa: BLE001` suppressions
- **Inconsistent error messages**: No centralized error rendering (mix of `f"Error: {exc}"` and `f"Unexpected error: {exc}"`)
- **No state transition suggestions**: Unlike tasks.py which suggests valid next actions
- **Missing error routing**: No typed exception handlers for specific error types

**tasks.py established pattern**:
- `with_task_error_handling` decorator for centralized exception handling
- `dispatch_exception()` routes errors to appropriate typed handlers
- `render_error()` provides consistent error formatting with verbose mode support
- 11 specialized handlers for different exception types with contextual suggestions
- Clean command definitions (no inline try/except blocks)

**Divergence risk**:
- New contributors see two different error handling patterns in same codebase
- projects.py has 395 lines but still growing (project tagging, switching, more registry features planned)
- Without unified error handling, projects.py will accumulate more ad-hoc try/except blocks
- Quality divergence makes codebase harder to maintain and extend

## What Changes

Unify `projects.py` error handling to match the sophisticated pattern established in `tasks.py`:

**Add error handling infrastructure**:
1. Create `with_project_error_handling` decorator (similar to tasks.py pattern)
2. Add `dispatch_exception()` for error routing
3. Add `render_error()` for consistent error formatting with verbose mode
4. Create specialized handlers for project-specific exceptions:
   - `handle_project_not_found_error`
   - `handle_backend_not_registered_error`
   - `handle_storage_error`
   - `handle_validation_error`
   - `handle_generic_error`

**Refactor commands**:
- Apply `@with_project_error_handling` decorator to all commands
- Remove inline try/except blocks (8 total)
- Let decorator handle exception routing and error rendering

**Add verbose mode support**:
- Add `--verbose` flag to project commands (matching tasks.py pattern)
- Show stack traces when `--verbose` is enabled
- Store verbose state in typer context for handler access

**Benefits**:
- **Consistency**: Projects and tasks commands use identical error handling pattern
- **Maintainability**: Future commands just apply decorator, no inline error handling
- **User experience**: Consistent error messages and verbose mode across all CLI commands
- **Code quality**: Remove 8 duplicate try/except blocks, eliminate `# noqa: BLE001` suppressions

## Impact

- **Affected specs**: `project-cli-operations` (add error handling requirements), `cli-error-presentation` (extend to projects)
- **Affected code**:
  - `packages/tasky-cli/src/tasky_cli/commands/projects.py` - add error handling infrastructure, refactor commands
  - Line reduction: ~30-40 lines (remove duplicate try/except blocks, add shared handlers is net positive)
- **Backward compatibility**: Zero breaking changes (error handling behavior improves but CLI interface unchanged)
- **Testing**: All existing tests must pass; error handling tests should be added for verbose mode and exception routing
- **Future work**: If tasks/projects error handling becomes identical, could extract to shared module (not in this change)
