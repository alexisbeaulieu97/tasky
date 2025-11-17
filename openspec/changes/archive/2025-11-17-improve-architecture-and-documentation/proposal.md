# Change: Improve Architecture and Documentation

## Why

The codebase has grown significantly with Phases 1-6, and several architectural issues have accumulated:
- Circular import risks due to poor module organization (local imports needed)
- Tight coupling between domain and infrastructure layers (TaskService depends on StorageDataError)
- High cyclomatic complexity in CLI commands and registry operations (marked with noqa: C901)
- Incomplete docstrings on private methods and helpers
- No Architecture Decision Records (ADRs) documenting key design choices

These issues make the codebase harder to maintain, refactor, and understand. New contributors struggle to understand the design rationale.

## What Changes

- Refactor module organization to eliminate circular imports
- Define error protocols to decouple domain from infrastructure
- Refactor high-complexity functions into smaller, testable pieces
- Add comprehensive docstrings to all public and key private functions
- Create ADR template and document key architectural decisions
- Simplify CLI command logic by extracting presentation concerns

## Impact

- **Affected specs**: New spec for `project-structure` and `documentation`
- **Affected code**: Multiple modules across all packages
- **Backward compatibility**: No breaking changes; refactoring only
- **Developer experience**: Easier to understand and maintain codebase
