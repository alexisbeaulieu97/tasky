# Change: Split Tasks CLI Module for Maintainability

## Why

The `tasks.py` CLI command module has grown to 991 lines with significant complexity issues:

- **Size**: 991 lines (largest file in codebase)
- **Complexity**: `list_command()` has 191 lines with cyclomatic complexity warnings (`noqa: C901, PLR0912, PLR0915`)
- **Mixed concerns**: Command definitions + error handling (11 handlers) + input validation + output formatting + business logic all in one file
- **Maintenance burden**: Adding new features (output formats, filters) or modifying error handling requires navigating the entire large file
- **Testing friction**: Complex monolithic structure makes it harder to test components in isolation
- **Pattern divergence risk**: As `projects.py` grows, lack of modular structure creates inconsistent patterns across CLI

This is a classic "code quality at inflection point" issue: the file grew organically during feature development but now needs intentional structure to support future growth (output formats, additional filters, MCP integration, etc.).

## What Changes

Refactor `tasky-cli/src/tasky_cli/commands/tasks.py` into a focused module structure:

```
tasky_cli/commands/tasks/
  __init__.py              # Public API, command registration
  commands.py              # Command definitions (create, list, show, update, etc.)
  error_handling.py        # Exception handlers and error rendering
  formatting.py            # Output formatting and display logic
  validation.py            # Input validation helpers
```

**Key principles**:
- **Behavioral equivalence**: No changes to CLI interface, output format, or error messages
- **Gradual refactor**: Extract modules one at a time with tests validating equivalence after each step
- **Clear separation**: Each module has single responsibility
- **Maintainability**: Future features (e.g., JSON output format) only touch relevant module

## Impact

- **Affected specs**: `task-cli-operations`, `cli-error-presentation`, `task-error-handling`
- **Affected code**:
  - `packages/tasky-cli/src/tasky_cli/commands/tasks.py` → split into module
  - All CLI tests continue to pass without modification (behavioral equivalence)
- **Backward compatibility**: Zero breaking changes (purely internal refactoring)
- **Testing**: All existing 577 tests must pass; add module-level unit tests for validation/formatting
- **Documentation**: Update module docstrings and architecture docs
