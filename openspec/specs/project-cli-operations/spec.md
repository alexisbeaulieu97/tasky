# project-cli-operations Specification

## Purpose
Define the CLI surface for managing projects, including initializing new projects, displaying the current project's configuration, and discovering other Tasky projects within a filesystem tree.
## Requirements
### Requirement: Display project configuration

The system SHALL provide commands to display project configuration for the current directory and to discover other Tasky projects.

- `tasky project info` SHALL show configuration for the current project directory (existing behavior).
- `tasky project list` SHALL discover and report all Tasky projects reachable from the chosen search scope.

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

---

### Requirement: Project List Command Discovers Local Projects

The system SHALL provide a `tasky project list` command that discovers and displays Tasky projects in the filesystem.

#### Scenario: List projects in current directory and parents

- **Given** multiple `.tasky` projects in current directory and parent directories
- **When** the user runs `tasky project list`
- **Then** the CLI SHALL search from the current directory upward to the filesystem root
- **And** the CLI SHALL display all discovered projects with their path, backend, and storage location
- **And** the CLI SHALL display "Found N projects" message at the end of the output

#### Scenario: List projects with recursive search

- **Given** a directory tree with projects at multiple nesting levels
- **When** the user runs `tasky project list --recursive`
- **Then** the CLI SHALL search the entire subtree recursively and discover every `.tasky` directory
- **And** results SHALL be sorted by project path

#### Scenario: List projects from custom root directory

- **Given** projects exist under `/some/custom/path`
- **When** the user runs `tasky project list --root /some/custom/path`
- **Then** the CLI SHALL search from the specified directory upward (default behavior) and report discovered projects

#### Scenario: List projects with custom root and recursive search

- **Given** projects exist at various depths under `/workspace`
- **When** the user runs `tasky project list --root /workspace --recursive`
- **Then** the CLI SHALL search the entire `/workspace` subtree and display all discovered projects sorted by path

---

### Requirement: Project List Displays Project Details

The system SHALL output consistent, scannable information for each discovered project.

#### Scenario: Display project location and configuration

- **Given** a project at `/home/user/myproject` with backend `json` and storage `tasks.json`
- **When** the user runs `tasky project list`
- **Then** the CLI SHALL output:
  ```
  Project: /home/user/myproject
  Backend: json
  Storage: tasks.json
  ```

#### Scenario: Display multiple projects in sorted order

- **Given** three projects at different locations with different backends
- **When** the user runs `tasky project list --recursive`
- **Then** all projects SHALL be displayed in a consistent format with entries clearly separated
- **And** projects SHALL be sorted alphabetically by their path

---

### Requirement: Project List Provides Count and Status Feedback

The system SHALL communicate how many projects were found and whether the search succeeded.

#### Scenario: Display count of projects found

- **Given** five projects are discovered
- **When** the user runs `tasky project list`
- **Then** the CLI SHALL display "Found 5 projects" at the end of the output (or "Found 1 project" when applicable)

#### Scenario: Show helpful message when no projects found

- **Given** no `.tasky` projects exist in the search scope
- **When** the user runs `tasky project list`
- **Then** the CLI SHALL display "No projects found. Run 'tasky project init' to create one." and exit successfully

---

### Requirement: Project List Supports Recursive and Root Options

The system SHALL expose flags to control project discovery scope.

#### Scenario: Accept --recursive flag

- **Given** the user runs `tasky project list --help`
- **Then** the help text SHALL document the `--recursive`/`-r` flag and explain that it searches all subdirectories recursively

#### Scenario: Accept --root option with directory path

- **Given** the user runs `tasky project list --help`
- **Then** the help text SHALL document the `--root PATH` option and explain that it chooses the starting directory for the search (default: current directory)

#### Scenario: Combine --root and --recursive

- **Given** projects exist at various depths under `/workspace`
- **When** the user runs `tasky project list --root /workspace --recursive`
- **Then** the CLI SHALL honor both options simultaneously and report all projects under `/workspace`

---

### Requirement: Project List Handles Edge Cases Gracefully

The system SHALL handle missing configs, invalid files, and permission errors without crashing.

#### Scenario: Skip directories with permission denied

- **Given** there is a project at `/home/user/project1` and an inaccessible directory `/root/project2`
- **When** the user runs `tasky project list --recursive`
- **Then** the CLI SHALL skip directories that raise `PermissionError` and continue discovering accessible projects

#### Scenario: Handle missing or malformed config files

- **Given** a `.tasky/config.toml` file is corrupted
- **When** the user runs `tasky project list`
- **Then** the CLI SHALL skip the malformed project (optionally logging a warning) and continue listing other valid projects

---

### Requirement: Backend validation during init

The system SHALL validate backend availability before creating configuration.

#### Scenario: List available backends in help text

```gherkin
When I run "tasky project init --help"
Then the help text includes:
  """
  --backend, -b TEXT  Storage backend (default: json)
                      Available: json, sqlite
  """
```

#### Scenario: Validate backend is registered

```gherkin
Given only "json" backend is registered
When I run "tasky project init --backend json"
Then the command succeeds
When I run "tasky project init --backend fake"
Then the command fails with "Backend 'fake' not found"
```

---
