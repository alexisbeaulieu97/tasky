# Spec: Project Registry Capability

**Capability**: `project-registry-capability`
**Status**: Draft
**Package**: `tasky-projects`
**Layer**: Domain

## Overview

The Project Registry capability enables tasky to discover, register, and manage multiple projects globally. It provides a central registry at `~/.tasky/registry.json` that tracks all known projects, their locations, and metadata. Users can list projects from anywhere, manually register new projects, and automatically discover projects in common locations.

This is the foundational capability for multi-project workflows, enabling future features like project switching and cross-project queries.

---

## ADDED Requirements

### Requirement: Project Registry Domain Models

The system MUST define domain models for project metadata and the global registry.

**Rationale**: Clean domain models separate project concerns from configuration, enabling rich metadata and future extensibility without changing persistence format.

#### Scenario: Create project metadata with required fields

**Given** a project located at `/home/user/code/website` with a `.tasky/` directory
**When** creating `ProjectMetadata` for the project
**Then** the metadata MUST include:
- `name`: "website" (derived from path basename)
- `path`: `/home/user/code/website` (absolute path to project root)
- `created_at`: ISO-8601 timestamp of first registration
- `last_accessed`: ISO-8601 timestamp of most recent use
- `tags`: empty list (reserved for future use)

#### Scenario: Project metadata serializes to JSON

**Given** a `ProjectMetadata` instance with all fields populated
**When** serializing to JSON using Pydantic
**Then** the output MUST be valid JSON
**And** deserializing the JSON MUST produce an equivalent instance
**And** datetime fields MUST use ISO-8601 format

#### Scenario: Project registry contains list of projects

**Given** three registered projects
**When** creating a `ProjectRegistry` instance
**Then** the registry MUST contain:
- `projects`: list of `ProjectMetadata` instances
- `registry_version`: "1.0" (schema version for future migrations)

#### Scenario: Registry validates unique projects by path

**Given** a registry with a project at `/home/user/code/website`
**When** attempting to add another project with the same path
**Then** the registry MUST update the existing entry, not create a duplicate
**And** the `last_accessed` timestamp MUST be updated

---

### Requirement: Project Registry Service Persistence

The system MUST provide a service that persists the project registry to a JSON file.

**Rationale**: Centralized service ensures atomic writes, consistent error handling, and lazy loading for performance.

#### Scenario: Load registry from file on first access

**Given** a registry file exists at `~/.tasky/registry.json`
**When** the service is accessed for the first time
**Then** the service MUST read and parse the JSON file
**And** the service MUST cache the registry in memory
**And** subsequent accesses MUST NOT re-read the file

#### Scenario: Create empty registry if file missing

**Given** no registry file exists at `~/.tasky/registry.json`
**When** the service loads the registry
**Then** the service MUST create an empty registry with:
- `projects`: empty list
- `registry_version`: "1.0"
**And** the empty registry MUST NOT be written to disk yet (lazy write)

#### Scenario: Save registry atomically to prevent corruption

**Given** a registry with modified project list
**When** saving the registry to disk
**Then** the service MUST:
1. Write to a temporary file (`registry.tmp`)
2. Verify the write succeeded
3. Atomically rename temp file to `registry.json` (POSIX atomic rename)
**And** if any step fails, the original file MUST remain unchanged

#### Scenario: Recover from corrupted registry file

**Given** a registry file with invalid JSON (corrupted)
**When** the service attempts to load the registry
**Then** the service MUST log an error message
**And** the service MUST create a fresh empty registry
**And** the service MUST back up the corrupted file as `registry.json.corrupted.{timestamp}`
**And** normal operation MUST continue without user intervention

---

### Requirement: Project Registration and Management

The service MUST provide CRUD operations for managing projects in the registry.

**Rationale**: Basic operations enable manual project management and serve as building blocks for discovery features.

#### Scenario: Register new project successfully

**Given** a project exists at `/home/user/code/website` with `.tasky/` directory
**When** calling `register_project(Path("/home/user/code/website"))`
**Then** the service MUST create a `ProjectMetadata` entry with:
- `name`: "website"
- `path`: `/home/user/code/website` (absolute)
- `created_at`: current timestamp
- `last_accessed`: current timestamp
**And** the entry MUST be added to the registry
**And** the registry MUST be saved to disk

#### Scenario: Register project validates path exists

**Given** a path `/home/user/code/nonexistent` that does not exist
**When** calling `register_project(Path("/home/user/code/nonexistent"))`
**Then** the service MUST raise `ValueError` with message: "Path does not exist"
**And** the registry MUST NOT be modified

#### Scenario: Register project validates .tasky directory exists

**Given** a path `/home/user/code/not-a-project` that exists but has no `.tasky/` directory
**When** calling `register_project(Path("/home/user/code/not-a-project"))`
**Then** the service MUST raise `ValueError` with message: "Not a tasky project (missing .tasky directory)"
**And** the registry MUST NOT be modified

#### Scenario: Update existing project registration

**Given** a project "website" already registered at `/home/user/code/website`
**When** calling `register_project(Path("/home/user/code/website"))` again
**Then** the service MUST update the existing entry (not create duplicate)
**And** the `last_accessed` timestamp MUST be updated to current time
**And** the `created_at` timestamp MUST remain unchanged
**And** the registry MUST be saved to disk

#### Scenario: Unregister project by path

**Given** a project "website" registered at `/home/user/code/website`
**When** calling `unregister_project(Path("/home/user/code/website"))`
**Then** the service MUST remove the project from the registry
**And** the registry MUST be saved to disk
**And** subsequent calls to `get_project("website")` MUST return None

#### Scenario: Unregister non-existent project fails gracefully

**Given** no project registered at `/home/user/code/nonexistent`
**When** calling `unregister_project(Path("/home/user/code/nonexistent"))`
**Then** the service MUST raise `ValueError` with message: "Project not found in registry"
**And** the registry MUST NOT be modified

#### Scenario: Get project by name

**Given** a project "website" registered at `/home/user/code/website`
**When** calling `get_project("website")`
**Then** the service MUST return the `ProjectMetadata` instance
**And** the metadata MUST have `name` == "website"
**And** the metadata MUST have correct path

#### Scenario: Get non-existent project returns None

**Given** no project named "nonexistent" in the registry
**When** calling `get_project("nonexistent")`
**Then** the service MUST return None

#### Scenario: List all projects returns sorted list

**Given** three projects registered: "api", "website", "scripts"
**And** "website" was accessed most recently
**And** "api" was accessed second most recently
**And** "scripts" was accessed least recently
**When** calling `list_projects()`
**Then** the service MUST return a list of three `ProjectMetadata` instances
**And** the list MUST be sorted by `last_accessed` descending
**And** the order MUST be: ["website", "api", "scripts"]

#### Scenario: Update last accessed timestamp

**Given** a project "website" with `last_accessed` = "2025-11-11T10:00:00Z"
**When** calling `update_last_accessed(Path("/home/user/code/website"))`
**Then** the project's `last_accessed` MUST be updated to current timestamp
**And** no other fields MUST change
**And** the registry MUST be saved to disk

---

### Requirement: Project Discovery

The service MUST automatically discover tasky projects in the filesystem.

**Rationale**: Manual registration is tedious and error-prone. Automatic discovery makes multi-project workflows seamless.

#### Scenario: Discover projects in search paths

**Given** search paths: [`/home/user/projects`, `/home/user/workspace`]
**And** `/home/user/projects/website/.tasky/` exists
**And** `/home/user/workspace/api/.tasky/` exists
**And** `/home/user/workspace/scripts/.tasky/` exists
**When** calling `discover_projects([Path("/home/user/projects"), Path("/home/user/workspace")])`
**Then** the service MUST return a list of 3 `ProjectMetadata` instances
**And** the list MUST include projects: "website", "api", "scripts"
**And** each project's path MUST be absolute
**And** each project MUST have valid `created_at` and `last_accessed` timestamps

#### Scenario: Discovery respects max depth limit

**Given** a search path `/home/user/projects`
**And** nested structure: `/home/user/projects/a/b/c/d/.tasky/` (depth 4)
**When** calling `discover_projects([Path("/home/user/projects")])` with max_depth=3
**Then** the service MUST NOT discover the project at depth 4
**And** the returned list MUST be empty

#### Scenario: Discovery skips common non-project directories

**Given** a search path `/home/user/projects`
**And** directories: `node_modules/.tasky/`, `.git/.tasky/`, `venv/.tasky/`, `__pycache__/.tasky/`
**When** calling `discover_projects([Path("/home/user/projects")])`
**Then** the service MUST skip all directories named:
- `node_modules`
- `.git`
- `venv`, `.venv`
- `__pycache__`
- `target`
- `build`
**And** the returned list MUST be empty

#### Scenario: Discovery handles permission errors gracefully

**Given** a search path `/home/user/projects`
**And** a subdirectory `/home/user/projects/restricted` with no read permission
**When** calling `discover_projects([Path("/home/user/projects")])`
**Then** the service MUST skip the restricted directory
**And** the service MUST log a warning message
**And** the service MUST continue discovery in other directories
**And** the service MUST NOT raise an exception

#### Scenario: Discovery deduplicates projects

**Given** search paths: [`/home/user/projects`, `/home/user/projects/subdir`]
**And** a project at `/home/user/projects/website/.tasky/`
**When** calling `discover_projects([Path("/home/user/projects"), Path("/home/user/projects/subdir")])`
**Then** the service MUST return only one entry for "website"
**And** the path MUST be `/home/user/projects/website`

#### Scenario: Auto-discover and register on first list

**Given** an empty registry (no projects registered)
**And** discovery paths configured in settings
**When** calling `discover_and_register(discovery_paths)`
**Then** the service MUST call `discover_projects()` with configured paths
**And** the service MUST register each discovered project
**And** the service MUST return count of newly registered projects
**And** subsequent calls MUST NOT re-discover (use cached registry)

---

### Requirement: CLI List Projects Command

The CLI MUST provide a `tasky project list` command to display all registered projects.

**Rationale**: Users need to see what projects exist and where they are located for navigation and context switching.

#### Scenario: List projects with formatted output

**Given** three projects registered: "website", "api", "scripts"
**When** running `tasky project list`
**Then** the output MUST display each project with:
- Project name (left-aligned)
- Project path (relative to home directory if possible)
- Last accessed timestamp (human-readable format)
**And** projects MUST be sorted by last accessed (most recent first)
**And** the output format MUST be:
```
Projects:
  website     ~/code/website         Last accessed: 2025-11-12 10:30
  api         ~/work/api-server      Last accessed: 2025-11-11 15:45
  scripts     ~/scripts              Last accessed: 2025-11-10 09:00
```

#### Scenario: List triggers auto-discovery on first use

**Given** no registry file exists at `~/.tasky/registry.json`
**And** discovery paths are configured
**When** running `tasky project list` for the first time
**Then** the CLI MUST display: "Discovering projects..."
**And** the CLI MUST call `discover_and_register()`
**And** the CLI MUST display: "Found N projects"
**And** the CLI MUST display the list of discovered projects
**And** subsequent runs MUST NOT trigger discovery (use cached registry)

#### Scenario: List shows empty message when no projects found

**Given** an empty registry (no projects)
**And** discovery returns no projects
**When** running `tasky project list`
**Then** the CLI MUST display: "No projects found."
**And** the CLI MUST display: "Run 'tasky project init' to create a project or 'tasky project discover' to scan for existing projects."
**And** the CLI MUST exit with status code 0

#### Scenario: List supports --no-discover flag

**Given** an empty registry
**When** running `tasky project list --no-discover`
**Then** the CLI MUST NOT call `discover_and_register()`
**And** the CLI MUST display: "No projects found."
**And** the CLI MUST exit with status code 0

#### Scenario: List validates project paths still exist

**Given** a project "old-project" registered at `/home/user/deleted-project`
**And** the path no longer exists on disk
**When** running `tasky project list`
**Then** the CLI MUST display the project with a warning indicator
**And** the output MUST show: "old-project     ~/deleted-project     [MISSING]"
**And** the CLI MUST exit with status code 0

---

### Requirement: CLI Register Project Command

The CLI MUST provide a `tasky project register` command to manually add projects to the registry.

**Rationale**: Manual registration enables users to add projects outside discovery paths or force registration of specific projects.

#### Scenario: Register project by path

**Given** a project exists at `/home/user/code/new-project` with `.tasky/` directory
**When** running `tasky project register /home/user/code/new-project`
**Then** the CLI MUST register the project in the registry
**And** the CLI MUST display: "✓ Project registered: new-project"
**And** the CLI MUST exit with status code 0

#### Scenario: Register project with relative path

**Given** current directory is `/home/user/code`
**And** a project exists at `./new-project/.tasky/`
**When** running `tasky project register ./new-project`
**Then** the CLI MUST resolve the path to absolute: `/home/user/code/new-project`
**And** the CLI MUST register the project
**And** the CLI MUST display: "✓ Project registered: new-project"

#### Scenario: Register project validates path exists

**Given** no directory at `/home/user/code/nonexistent`
**When** running `tasky project register /home/user/code/nonexistent`
**Then** the CLI MUST display error: "Error: Path does not exist: /home/user/code/nonexistent"
**And** the CLI MUST exit with status code 1
**And** the registry MUST NOT be modified

#### Scenario: Register project validates .tasky directory

**Given** a directory at `/home/user/code/not-a-project` without `.tasky/`
**When** running `tasky project register /home/user/code/not-a-project`
**Then** the CLI MUST display error: "Error: Not a tasky project (missing .tasky directory)"
**And** the CLI MUST suggest: "Run 'tasky project init' in that directory first."
**And** the CLI MUST exit with status code 1

#### Scenario: Register already registered project updates metadata

**Given** a project "website" already registered
**When** running `tasky project register /home/user/code/website`
**Then** the CLI MUST update the existing entry
**And** the CLI MUST display: "✓ Project updated: website"
**And** the `last_accessed` timestamp MUST be updated

---

### Requirement: CLI Unregister Project Command

The CLI MUST provide a `tasky project unregister` command to remove projects from the registry.

**Rationale**: Users need to remove projects they no longer work on or that have been moved/deleted.

#### Scenario: Unregister project by name

**Given** a project "old-project" registered in the registry
**When** running `tasky project unregister old-project`
**Then** the CLI MUST prompt: "Remove 'old-project' from registry? [y/N]"
**And** if user confirms with 'y'
**Then** the CLI MUST remove the project from the registry
**And** the CLI MUST display: "✓ Project unregistered: old-project"
**And** the CLI MUST exit with status code 0

#### Scenario: Unregister with --yes flag skips confirmation

**Given** a project "old-project" registered
**When** running `tasky project unregister old-project --yes`
**Then** the CLI MUST NOT prompt for confirmation
**And** the CLI MUST remove the project immediately
**And** the CLI MUST display: "✓ Project unregistered: old-project"

#### Scenario: Unregister non-existent project shows error

**Given** no project named "nonexistent" in the registry
**When** running `tasky project unregister nonexistent`
**Then** the CLI MUST display error: "Error: Project not found: nonexistent"
**And** the CLI MUST suggest: "Run 'tasky project list' to see registered projects."
**And** the CLI MUST exit with status code 1

#### Scenario: Unregister does not delete project files

**Given** a project "website" registered at `/home/user/code/website`
**When** running `tasky project unregister website --yes`
**Then** the project MUST be removed from the registry
**But** the directory `/home/user/code/website` MUST still exist
**And** the `.tasky/` directory MUST still exist
**And** the CLI MUST display note: "Note: Project files not deleted. Only removed from registry."

---

### Requirement: CLI Discover Projects Command

The CLI MUST provide a `tasky project discover` command to scan for and register projects.

**Rationale**: Explicit discovery gives users control over when scanning happens and what paths to search.

#### Scenario: Discover projects in default paths

**Given** discovery paths configured in settings: `~/projects`, `~/workspace`
**And** projects exist in those locations
**When** running `tasky project discover`
**Then** the CLI MUST display: "Discovering projects in:"
**And** the CLI MUST list each search path
**And** the CLI MUST show progress indicator during scan
**And** the CLI MUST display summary: "Discovered N projects, registered M new"
**And** the CLI MUST list newly registered projects with paths

#### Scenario: Discover projects in custom paths

**Given** default discovery paths are `~/projects`
**When** running `tasky project discover --paths ~/work,~/personal`
**Then** the CLI MUST search only in `~/work` and `~/personal`
**And** the CLI MUST NOT search in `~/projects`
**And** the CLI MUST display paths being searched
**And** the CLI MUST display results from those paths only

#### Scenario: Discover shows progress for long scans

**Given** a discovery path with 1000+ directories
**When** running `tasky project discover`
**Then** the CLI MUST show a progress indicator (spinner or progress bar)
**And** the CLI MUST update the indicator during the scan
**And** the CLI MUST display: "Scanning... (N directories checked)"
**And** the scan MUST complete in <2 seconds for typical use cases

#### Scenario: Discover handles no new projects found

**Given** all existing projects already registered
**When** running `tasky project discover`
**Then** the CLI MUST display: "Discovered 3 projects, registered 0 new"
**And** the CLI MUST display: "All discovered projects are already registered."
**And** the CLI MUST exit with status code 0

#### Scenario: Discover shows errors for inaccessible paths

**Given** a discovery path `/restricted` with no read permission
**When** running `tasky project discover`
**Then** the CLI MUST display warning: "Warning: Cannot access /restricted (permission denied)"
**And** the CLI MUST continue discovery in other paths
**And** the CLI MUST complete successfully

---

### Requirement: CLI Info Command Project Support

The existing `tasky project info` command MUST be enhanced to support querying registered projects by name.

**Rationale**: Users need to inspect project details without navigating to the project directory.

#### Scenario: Info shows current project details

**Given** current directory is `/home/user/code/website` with `.tasky/` directory
**When** running `tasky project info` (no arguments)
**Then** the CLI MUST display current project information (existing behavior)
**And** the output MUST include: path, created_at, backend, storage path
**And** the CLI MUST exit with status code 0

#### Scenario: Info shows named project details

**Given** a project "api" registered at `/home/user/work/api-server`
**When** running `tasky project info api`
**Then** the CLI MUST look up "api" in the registry
**And** the CLI MUST display project information:
```
Project: api
  Path: /home/user/work/api-server
  Created: 2025-10-15 09:12
  Last accessed: 2025-11-11 15:45
  Backend: json
  Storage: tasks.json
```
**And** the CLI MUST exit with status code 0

#### Scenario: Info handles non-existent project name

**Given** no project named "nonexistent" in the registry
**When** running `tasky project info nonexistent`
**Then** the CLI MUST display error: "Error: Project not found: nonexistent"
**And** the CLI MUST suggest: "Run 'tasky project list' to see registered projects."
**And** the CLI MUST exit with status code 1

---

### Requirement: Registry Performance

The registry MUST perform efficiently for typical and large project counts.

**Rationale**: Poor performance would discourage use and limit scalability.

#### Scenario: List projects responds quickly

**Given** a registry with 100 projects
**When** running `tasky project list`
**Then** the CLI MUST load the registry in <100ms
**And** the CLI MUST display results in <200ms total
**And** the user MUST perceive instant response

#### Scenario: Discovery scans efficiently

**Given** 1000 directories in search paths
**And** 10 projects scattered throughout
**When** running `tasky project discover`
**Then** the discovery MUST complete in <2 seconds
**And** the CLI MUST show progress during scan
**And** the CLI MUST skip common non-project directories

#### Scenario: Registry scales to hundreds of projects

**Given** a registry with 500 projects
**When** running `tasky project list`
**Then** the CLI MUST load and display all projects
**And** the response time MUST be <500ms
**And** the registry file MUST be <1MB in size
**And** memory usage MUST be <50MB

---

## Implementation Notes

### File Locations
- Domain models: `packages/tasky-projects/src/tasky_projects/models.py`
- Registry service: `packages/tasky-projects/src/tasky_projects/registry.py`
- CLI commands: `packages/tasky-cli/src/tasky_cli/commands/projects.py`
- Registry file: `~/.tasky/registry.json`

### Settings Configuration
```python
# packages/tasky-settings/src/tasky_settings/config.py
class Settings(BaseSettings):
    registry_path: Path = Path("~/.tasky/registry.json")
    discovery_paths: list[Path] = [
        Path("~/projects"),
        Path("~/workspace"),
        Path("~/dev"),
        Path("~/src"),
        Path("~/code"),
    ]
```

### Discovery Skip List
Directories to skip during discovery:
- `.git`, `.svn`, `.hg` (version control)
- `node_modules`, `bower_components` (JavaScript)
- `venv`, `.venv`, `virtualenv` (Python)
- `__pycache__`, `*.pyc` (Python cache)
- `target` (Rust, Java)
- `build`, `dist` (build artifacts)
- `.tox`, `.nox` (test environments)

### Error Messages
Consistent error message format:
```
Error: <problem description>
<optional suggestion or next step>
```

Examples:
- "Error: Path does not exist: /path/to/nonexistent"
- "Error: Not a tasky project (missing .tasky directory)"
  "Run 'tasky project init' in that directory first."
- "Error: Project not found: project-name"
  "Run 'tasky project list' to see registered projects."

---

## Testing Requirements

### Unit Tests
- Test `ProjectMetadata` creation and validation
- Test `ProjectRegistry` uniqueness enforcement
- Test `ProjectRegistryService` CRUD operations
- Test discovery algorithm with mock filesystem
- Test atomic write mechanism

**Test Files**:
- `packages/tasky-projects/tests/test_models.py`
- `packages/tasky-projects/tests/test_registry.py`
- `packages/tasky-projects/tests/test_discovery.py`

### Integration Tests
- Test registry persistence with real JSON files
- Test discovery with real directory structures
- Test service factory from settings
- Test concurrent access scenarios
- Test recovery from corrupted registry

**Test File**:
- `packages/tasky-projects/tests/test_integration.py`

### End-to-End Tests
- Test all CLI commands with real service
- Test auto-discovery on first `list`
- Test manual register/unregister workflow
- Test explicit discover command
- Test info command with project names

**Test File**:
- `packages/tasky-cli/tests/test_project_registry.py`

### Performance Tests
- Test discovery with 1000+ directories
- Test registry with 100+ projects
- Measure load time, save time, discovery time

### Edge Case Tests
- Permission errors during discovery
- Symlinks in project paths
- Paths with spaces and special characters
- Registry file in read-only directory
- Corrupted registry file
- Duplicate project names (different paths)

---

## User Experience Considerations

### First-Time Experience
1. User runs `tasky project list` for first time
2. System displays: "Discovering projects..."
3. System finds projects and shows: "Found N projects"
4. System displays the list
5. Future runs skip discovery (use cache)

### Progressive Enhancement
- Start with manual registration (`register` command)
- Add auto-discovery for convenience (`list` triggers it)
- Add explicit discovery for control (`discover` command)
- Future: Add project switching, cross-project queries

### Helpful Defaults
- Registry in standard location (`~/.tasky/registry.json`)
- Discovery in common dev directories (`~/projects`, etc.)
- Sensible depth limit (3 levels)
- Skip common non-project directories automatically

### Clear Feedback
- Show what's happening during long operations
- Confirm destructive actions (unregister)
- Provide next steps in error messages
- Use consistent formatting across commands

---

## Related Capabilities

### Dependencies
- `project-configuration`: Projects must have `.tasky/config.toml`
- `storage-configuration`: Registry needs to understand backend types
- `hierarchical-settings`: Registry path from settings

### Enables
- Future: `project-switching`: Change active project context
- Future: `cross-project-queries`: Query tasks across projects
- Future: `project-templates`: Initialize projects from templates
- Future: `project-analytics`: Aggregate statistics across projects

---

## Migration Path

**Current State**: No registry exists, `tasky project list` is a stub

**After This Change**:
- Registry file created on first use
- Auto-discovery populates registry automatically
- All existing functionality preserved (no breaking changes)

**For Existing Users**:
1. First `tasky project list` discovers existing projects
2. Projects are automatically registered
3. No manual migration required

**For New Users**:
1. Run `tasky project init` to create first project
2. Run `tasky project list` to see it registered
3. Add more projects naturally over time

---

## Future Enhancements

**Phase 6: Project Switching**
```bash
tasky switch website    # Change active project context
tasky task list         # Lists tasks from 'website' project
```

**Phase 7: Cross-Project Queries**
```bash
tasky task list --project=website      # Tasks from specific project
tasky task list --all-projects         # Tasks from all projects
tasky stats                             # Aggregate statistics
```

**Phase 8: Project Templates**
```bash
tasky project create my-app --template=python    # Initialize from template
tasky template list                              # Show available templates
```

**Future: Advanced Features**
- Project tags and filtering
- Remote registry synchronization
- Project archiving and cleanup
- Project relationships and dependencies
