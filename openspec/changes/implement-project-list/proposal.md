# Proposal: Implement Project List Command

**Change ID**: `implement-project-list`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant

## Overview

This proposal implements the `tasky project list` command to discover and display all .tasky projects within a directory tree. Currently, the stub exists but returns nothing. This change enables users to find all projects on their system or within a specified directory hierarchy, improving project discoverability and workspace navigation.

## Problem Statement

Users have no way to discover existing tasky projects on their system. The `tasky project list` command exists as a stub but doesn't work. Users must manually search the filesystem for `.tasky/config.toml` files or rely on external tools to find projects, which is cumbersome and error-prone.

## Why

Project discovery is essential for multi-project workflows:

- **Workspace Navigation**: Developers need to find projects quickly without manual filesystem searching
- **Project Inventory**: Users want to see all projects they've created and their configurations
- **Setup Verification**: After initialization, users should be able to confirm projects exist and see their details
- **System Cleanup**: Users need visibility into projects to manage, backup, or remove them

Without project listing, users lose context about their project ecosystem. This change provides the foundation for better project management and visibility.

## Proposed Solution

Implement project discovery at three layers:

1. **Project Registry Protocol**: Extend `ProjectRegistry` with discovery methods
2. **Project Locator Service**: Implement filesystem search logic for .tasky directories
3. **CLI**: Add `tasky project list` command with optional flags for customization

### User-Facing Changes

```bash
# List projects in current directory and parents (default)
tasky project list

# List projects recursively in subtree
tasky project list --recursive

# Search from specific directory
tasky project list --root /some/path

# Search from specific directory recursively
tasky project list --root /some/path --recursive
```

## Acceptance Criteria

1. Command finds all `.tasky/config.toml` files in search tree
2. Displays: project path, configured backend, storage location
3. Shows count: "Found N projects"
4. Supports `--root DIR` to search from specific location
5. Supports `--recursive` flag to search all subdirectories
6. Shows helpful message when no projects found
7. Searches upward from current directory by default
8. Results are displayed with consistent formatting
9. Test coverage ≥80% for all new functionality

## Non-Goals

- Configuration editing via `project list`
- Project filtering by backend type or other criteria
- Real-time monitoring of projects
- Project validation or health checks
- Automatic project import or registration

## Dependencies

This change depends on:
- Existing project domain models in `tasky-projects`
- Configuration loading from `.tasky/config.toml`

## Risks and Mitigations

**Risk**: Searching large directory trees could be slow
**Mitigation**: Implement efficient `os.walk()` with early termination. Add optional `--recursive` flag so default behavior is conservative (search upward only).

**Risk**: Finding projects across different storage backends might be complex
**Mitigation**: Look only for `.tasky/config.toml` structure, which is consistent. Configuration parsing already handles different backends.

## Alternatives Considered

1. **Scan only from home directory**: Rejected because users may have projects anywhere
2. **Require explicit project registration**: Rejected because discovery should be automatic
3. **Search recursively by default**: Rejected because it's slow and unexpected; make it opt-in

## Implementation Notes

- Use `os.walk()` for efficient filesystem traversal
- Stop searching upward at filesystem root or home directory
- Parse `.tasky/config.toml` to extract backend and storage info
- Handle permission errors gracefully
- Sort results for consistent output
- Provide clear, scannable output format

## Related Changes

- Foundation for future `project info` enhancements
- Enables future `project validate` or `project health-check` commands
- Supports future workspace management features

---

## Success Definition

- Users can discover projects with `tasky project list`
- Output clearly shows project location, backend, and storage path
- Command handles edge cases (no projects, permission denied, etc.)
- Performance is acceptable for typical filesystem structures
- All tests pass and code quality checks pass
