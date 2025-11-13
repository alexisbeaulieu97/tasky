# Spec Delta: Project CLI Operations - List Command

**Capability**: `project-cli-operations`
**Status**: Draft
**Package**: `tasky-cli` / `tasky-projects`
**Layer**: Presentation / Domain

## Overview

Extends the `project` command group with a `list` subcommand to discover and display all tasky projects within a filesystem tree. Enables users to explore their project landscape with optional recursive and custom root directory support.

---

## ADDED Requirements

### Requirement: Project List Command Discovers Local Projects

The system SHALL provide a `tasky project list` command that discovers and displays projects in the filesystem.

**Rationale**: Users need to discover existing projects without manual filesystem searching. This command provides project inventory and workspace visibility.

#### Scenario: List projects in current directory and parents

**Given** multiple `.tasky` projects in current directory and parent directories
**When** the user runs `tasky project list` (without flags)
**Then** the CLI SHALL search from current directory upward to root
**And** the CLI SHALL display all discovered projects
**And** each project SHALL show: path, configured backend, storage location
**And** the CLI SHALL display "Found N projects" message

#### Scenario: List projects with recursive search

**Given** a directory tree with projects at multiple nesting levels
**When** the user runs `tasky project list --recursive`
**Then** the CLI SHALL search entire subtree recursively
**And** the CLI SHALL find all `.tasky` projects regardless of depth
**And** the CLI SHALL display all discovered projects with full details
**And** results SHALL be sorted by project path

#### Scenario: List projects from custom root directory

**Given** projects exist under `/some/custom/path/`
**When** the user runs `tasky project list --root /some/custom/path`
**Then** the CLI SHALL search from specified directory upward
**And** only projects in `/some/custom/path` and parents SHALL be found
**And** output SHALL display discovered projects

#### Scenario: List projects with custom root and recursive

**Given** projects exist at various depths under `/workspace`
**When** the user runs `tasky project list --root /workspace --recursive`
**Then** the CLI SHALL search entire `/workspace` subtree recursively
**And** all projects at all nesting levels SHALL be discovered
**And** results SHALL be sorted consistently

---

### Requirement: Project List Displays Project Details

The system SHALL display consistent, scannable information for each discovered project.

**Rationale**: Users need to understand project configuration without opening files. Clear display enables quick decision-making about which project to work with.

#### Scenario: Display project location and configuration

**Given** a project at `/home/user/myproject` with JSON backend and storage at `tasks.json`
**When** the user runs `tasky project list`
**Then** the output SHALL include:
```
Project: /home/user/myproject
Backend: json
Storage: tasks.json
```
**And** formatting SHALL be consistent and scannable

#### Scenario: Display multiple projects in tabular format

**Given** three projects at different locations with different backends
**When** the user runs `tasky project list --recursive`
**Then** all projects SHALL be displayed in consistent format
**And** each project entry SHALL be clearly separated
**And** projects SHALL be sorted by path alphabetically

---

### Requirement: Project List Provides Count and Status Feedback

The system SHALL provide clear feedback about discovery results.

**Rationale**: Users should understand how many projects were found and whether the search succeeded or had issues.

#### Scenario: Display count of projects found

**Given** five projects discovered in search tree
**When** the user runs `tasky project list`
**Then** the CLI SHALL display "Found 5 projects" at end of output
**Or** if only one project: "Found 1 project"

#### Scenario: Show helpful message when no projects found

**Given** no `.tasky` projects exist in search tree
**When** the user runs `tasky project list`
**Then** the CLI SHALL display message: "No projects found. Run 'tasky project init' to create one."
**And** the CLI SHALL exit with status code 0 (success)
**And** no error message SHALL be shown

---

### Requirement: Project List Supports Recursive and Root Options

The system SHALL accept optional flags to customize project discovery scope.

**Rationale**: Different workflows require different search strategies. Upward search finds parent projects efficiently; recursive search explores entire subtrees; custom root enables workspace flexibility.

#### Scenario: Accept --recursive flag

**Given** the user runs `tasky project list --help`
**When** help text is displayed
**Then** the help text SHALL document `--recursive` flag
**And** flag description SHALL explain "Search all subdirectories recursively"
**And** default behavior (upward search) SHALL be documented

#### Scenario: Accept --root option with directory path

**Given** the user runs `tasky project list --help`
**When** help text is displayed
**Then** the help text SHALL document `--root` option
**And** option description SHALL explain "Search from specified directory (default: current directory)"
**And** option SHALL accept absolute or relative paths

#### Scenario: Combine --root and --recursive flags

**Given** the user runs `tasky project list --root /some/path --recursive`
**When** the command executes
**Then** search SHALL start from `/some/path`
**And** search SHALL traverse entire subtree recursively
**And** results SHALL include all projects under `/some/path`

---

### Requirement: Project List Handles Edge Cases Gracefully

The system SHALL handle permission errors, missing files, and invalid input without crashing.

**Rationale**: Robust error handling ensures users get clear feedback about issues without confusion or frustration.

#### Scenario: Skip directories with permission denied

**Given** project at `/home/user/project1` and inaccessible directory `/root/project2`
**When** the user runs `tasky project list --recursive`
**Then** the CLI SHALL skip permission-denied directories
**And** discovered projects SHALL be displayed normally
**And** no crash or exception SHALL occur

#### Scenario: Handle missing or malformed config files

**Given** a `.tasky/config.toml` file that is corrupted or unreadable
**When** the user runs `tasky project list`
**Then** the CLI SHALL skip the malformed project
**Or** the CLI SHALL display warning and continue
**And** other valid projects SHALL still be discovered

---

## MODIFIED Requirements

### Requirement: Display project configuration

**Modified Behavior**: Extend existing `project info` requirement to clarify relationship with new `project list` command.

The system SHALL provide a command to display the current project configuration (existing `tasky project info`) and a command to discover and list all projects (new `tasky project list`).

- `tasky project info` - Shows details of current/specified project
- `tasky project list` - Discovers and displays all projects in a tree

#### Scenario: Show project info

```gherkin
Given a project with config:
  """
  {
    "version": "1.0",
    "storage": {
      "backend": "json",
      "path": "tasks.json"
    },
    "created_at": "2025-11-11T10:00:00Z"
  }
  """
When I run "tasky project info"
Then the CLI outputs:
  """
  Project Configuration
  ---------------------
  Location: /home/user/myproject/.tasky
  Backend: json
  Storage: tasks.json
  Created: 2025-11-11 10:00:00+00:00
  """
```

#### Scenario: Show info when no project found

```gherkin
Given no ".tasky/config.json" exists
When I run "tasky project info"
Then it exits with error code 1
And the error message includes "No project found"
And the error message suggests "Run 'tasky project init' first"
```

#### Scenario: List discovers all projects in tree

```gherkin
Given multiple projects at:
  /home/user/project1/.tasky/config.toml
  /home/user/project2/.tasky/config.toml
  /home/user/work/project3/.tasky/config.toml
When I run "tasky project list --recursive"
Then the CLI outputs all three projects with their details
And the output includes "Found 3 projects"
```

---

## Implementation Notes

- Create: `packages/tasky-projects/src/tasky_projects/locator.py`
  - Implement `ProjectLocation` dataclass
  - Implement `find_projects_upward(start_dir: Path) -> List[ProjectLocation]`
  - Implement `find_projects_recursive(root_dir: Path) -> List[ProjectLocation]`

- Update: `packages/tasky-cli/src/tasky_cli/commands/projects.py`
  - Add `list_command()` function
  - Add `--recursive` boolean flag
  - Add `--root` string option
  - Integrate with locator service

- Output format (example):
  ```
  Project: /home/user/myproject
  Backend: json
  Storage: tasks.json

  Project: /home/user/work/myapp
  Backend: sqlite
  Storage: .tasky/tasks.db

  Found 2 projects
  ```

---

## Testing Requirements

- Unit tests for project locator:
  - Test upward search finds parent projects
  - Test recursive search finds nested projects
  - Test sorting of results
  - Test handling of missing/malformed configs

- CLI integration tests:
  - Test `tasky project list` (default upward search)
  - Test `--recursive` flag behavior
  - Test `--root` option with custom path
  - Test `--root` with `--recursive` combined
  - Test no projects found scenario
  - Test output formatting and count display
  - Test help text includes options

**Test Files**:
- `packages/tasky-projects/tests/test_locator.py`
- `packages/tasky-cli/tests/test_project_list.py`

---

## User Experience Considerations

- Default upward search is conservative and fast
- Recursive search is explicitly opt-in
- Custom root enables workspace flexibility
- Output is scannable and sortable
- Clear count gives users discovery confidence
- No-projects message suggests next action
- Error handling is graceful and informative

---

## Related Specifications

- `project-cli-operations`: Host specification (this requirement modifies it)
- `project-configuration`: Project metadata and config loading
- `storage-configuration`: Backend and storage configuration
