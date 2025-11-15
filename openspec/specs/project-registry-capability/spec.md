# project-registry-capability Specification

## Purpose
TBD - created by archiving change add-project-registry. Update Purpose after archive.
## Requirements
### Requirement: Project Registry Domain Models

The system SHALL define domain models for project metadata and the global registry.

#### Scenario: Create project metadata with required fields

- **GIVEN** a project located at `/home/user/code/website` with a `.tasky/` directory
- **WHEN** creating `ProjectMetadata` for the project
- **THEN** the metadata includes `name`, `path`, `created_at`, `last_accessed`, and `tags`

#### Scenario: Project metadata serializes to JSON

- **GIVEN** a `ProjectMetadata` instance with all fields populated
- **WHEN** serializing to JSON using Pydantic
- **THEN** the output is valid JSON with ISO-8601 datetime fields

#### Scenario: Project registry contains list of projects

- **GIVEN** three registered projects
- **WHEN** creating a `ProjectRegistry` instance
- **THEN** the registry contains `projects` list and `registry_version` "1.0"

#### Scenario: Registry validates unique projects by path

- **GIVEN** a registry with a project at `/home/user/code/website`
- **WHEN** attempting to add another project with the same path
- **THEN** the registry updates the existing entry instead of creating a duplicate

---

### Requirement: Project Registry Service Persistence

The system SHALL provide a service that persists the project registry to a JSON file.

#### Scenario: Load registry from file on first access

- **GIVEN** a registry file exists at `~/.tasky/registry.json`
- **WHEN** the service is accessed for the first time
- **THEN** the service reads and caches the registry in memory

#### Scenario: Create empty registry if file missing

- **GIVEN** no registry file exists at `~/.tasky/registry.json`
- **WHEN** the service loads the registry
- **THEN** the service creates an empty registry with default structure

#### Scenario: Save registry atomically to prevent corruption

- **GIVEN** a registry with modified project list
- **WHEN** saving the registry to disk
- **THEN** the service writes atomically to prevent corruption

#### Scenario: Recover from corrupted registry file

- **GIVEN** a registry file with invalid JSON
- **WHEN** the service attempts to load the registry
- **THEN** the service logs error, backs up corrupted file, and creates fresh registry

---

### Requirement: Project Registration and Management

The service SHALL provide CRUD operations for managing projects in the registry.

#### Scenario: Register new project successfully

- **GIVEN** a project exists at `/home/user/code/website` with `.tasky/` directory
- **WHEN** calling `register_project(Path("/home/user/code/website"))`
- **THEN** the project is added to the registry with metadata

#### Scenario: Register project validates path exists

- **GIVEN** a path that does not exist
- **WHEN** calling `register_project(Path("/home/user/code/nonexistent"))`
- **THEN** the service raises `ValueError` and registry is not modified

#### Scenario: Register project validates .tasky directory exists

- **GIVEN** a path that exists but has no `.tasky/` directory
- **WHEN** calling `register_project(Path("/home/user/code/not-a-project"))`
- **THEN** the service raises `ValueError` with descriptive message

#### Scenario: Update existing project registration

- **GIVEN** a project already registered
- **WHEN** calling `register_project()` with same path again
- **THEN** the `last_accessed` timestamp is updated, `created_at` unchanged

#### Scenario: Unregister project by path

- **GIVEN** a project registered in the registry
- **WHEN** calling `unregister_project(Path("/home/user/code/website"))`
- **THEN** the project is removed from the registry

#### Scenario: Get project by name

- **GIVEN** a project "website" registered
- **WHEN** calling `get_project("website")`
- **THEN** the service returns the `ProjectMetadata` instance

#### Scenario: List projects sorted by last access

- **GIVEN** three projects with different access times
- **WHEN** calling `list_projects()`
- **THEN** projects are returned sorted by `last_accessed` descending

#### Scenario: Update last accessed timestamp

- **GIVEN** a project with a previous `last_accessed` timestamp
- **WHEN** calling `update_last_accessed(path)`
- **THEN** the timestamp is updated to current time

---

### Requirement: Project Discovery

The service SHALL automatically discover tasky projects in the filesystem.

#### Scenario: Discover projects in search paths

- **GIVEN** search paths with multiple projects containing `.tasky/` directories
- **WHEN** calling `discover_projects(paths)`
- **THEN** all projects are found and returned with correct metadata

#### Scenario: Discovery respects max depth limit

- **GIVEN** a search path with nested directories beyond max_depth
- **WHEN** calling `discover_projects(paths)` with max_depth=3
- **THEN** projects deeper than max_depth are not discovered

#### Scenario: Discovery skips common non-project directories

- **GIVEN** a search path with `node_modules`, `.git`, `venv` directories
- **WHEN** calling `discover_projects(paths)`
- **THEN** excluded directories are skipped

#### Scenario: Discovery handles permission errors gracefully

- **GIVEN** a search path with restricted subdirectories
- **WHEN** calling `discover_projects(paths)`
- **THEN** restricted directories are skipped and discovery continues

#### Scenario: Discovery deduplicates projects

- **GIVEN** overlapping search paths with the same project
- **WHEN** calling `discover_projects(paths)`
- **THEN** each project appears only once in results

#### Scenario: Auto-discover and register on first use

- **GIVEN** an empty registry and configured discovery paths
- **WHEN** calling `discover_and_register(paths)`
- **THEN** projects are discovered and registered automatically

---

### Requirement: CLI List Projects Command

The CLI SHALL provide a `tasky project list` command to display all registered projects.

#### Scenario: List projects with formatted output

- **GIVEN** multiple projects registered
- **WHEN** running `tasky project list`
- **THEN** projects are displayed with name, path, and last accessed timestamp

#### Scenario: List triggers auto-discovery on first use

- **GIVEN** an empty registry on first use
- **WHEN** running `tasky project list`
- **THEN** discovery is triggered and projects are registered automatically

#### Scenario: List shows empty message when no projects

- **GIVEN** an empty registry with no projects
- **WHEN** running `tasky project list`
- **THEN** helpful message is displayed suggesting next steps

#### Scenario: List supports --no-discover flag

- **GIVEN** an empty registry
- **WHEN** running `tasky project list --no-discover`
- **THEN** discovery is skipped and empty message shown

#### Scenario: List validates project paths still exist

- **GIVEN** a project with deleted path
- **WHEN** running `tasky project list`
- **THEN** project is marked with `[MISSING]` indicator

#### Scenario: List supports --validate flag

- **GIVEN** multiple projects in registry
- **WHEN** running `tasky project list --validate`
- **THEN** all paths are checked and status reported

#### Scenario: List supports --clean flag

- **GIVEN** projects with missing paths
- **WHEN** running `tasky project list --clean`
- **THEN** stale entries are removed from registry

---

### Requirement: CLI Register Project Command

The CLI SHALL provide a `tasky project register` command to manually add projects to the registry.

#### Scenario: Register project by path

- **GIVEN** a project with `.tasky/` directory
- **WHEN** running `tasky project register /path/to/project`
- **THEN** project is registered and success message displayed

#### Scenario: Register project with relative path

- **GIVEN** current directory with a project subdirectory
- **WHEN** running `tasky project register ./project`
- **THEN** relative path is resolved to absolute and registered

#### Scenario: Register project validates path exists

- **GIVEN** a nonexistent path
- **WHEN** running `tasky project register /nonexistent`
- **THEN** error message displayed and registry unchanged

#### Scenario: Register project validates .tasky directory

- **GIVEN** a directory without `.tasky/`
- **WHEN** running `tasky project register /path`
- **THEN** descriptive error message displayed

#### Scenario: Register updates existing project

- **GIVEN** an already registered project
- **WHEN** running `tasky project register` with same path again
- **THEN** metadata is updated, success message shown

---

### Requirement: CLI Unregister Project Command

The CLI SHALL provide a `tasky project unregister` command to remove projects from the registry.

#### Scenario: Unregister project with confirmation

- **GIVEN** a registered project
- **WHEN** running `tasky project unregister project-name`
- **THEN** confirmation prompt shown before removal

#### Scenario: Unregister with --yes flag

- **GIVEN** a registered project
- **WHEN** running `tasky project unregister project-name --yes`
- **THEN** project removed without confirmation prompt

#### Scenario: Unregister non-existent project shows error

- **GIVEN** no project with the specified name
- **WHEN** running `tasky project unregister nonexistent`
- **THEN** error message displayed

#### Scenario: Unregister does not delete project files

- **GIVEN** a registered project at `/home/user/code/website`
- **WHEN** running `tasky project unregister website --yes`
- **THEN** project directory and files remain intact

---

### Requirement: CLI Discover Projects Command

The CLI SHALL provide a `tasky project discover` command to scan for and register projects.

#### Scenario: Discover projects in default paths

- **GIVEN** discovery paths configured in settings
- **WHEN** running `tasky project discover`
- **THEN** projects found in paths are discovered and registered

#### Scenario: Discover projects with progress indicator

- **GIVEN** discovery paths with multiple directories
- **WHEN** running `tasky project discover`
- **THEN** progress indicator shown during scan

#### Scenario: Discover shows no new projects message

- **GIVEN** all projects already registered
- **WHEN** running `tasky project discover`
- **THEN** message shown indicating no new projects

#### Scenario: Discover completes quickly

- **GIVEN** 1000+ directories in search paths
- **WHEN** running `tasky project discover`
- **THEN** discovery completes in under 2 seconds

---

### Requirement: CLI Info Command Project Support

The CLI SHALL enhance `tasky project info` to support querying registered projects by name.

#### Scenario: Info shows current project details

- **GIVEN** current directory is a tasky project
- **WHEN** running `tasky project info`
- **THEN** project details displayed (existing behavior)

#### Scenario: Info shows named project details

- **GIVEN** a project registered in the registry
- **WHEN** running `tasky project info project-name`
- **THEN** project information retrieved from registry and displayed

#### Scenario: Info handles non-existent project

- **GIVEN** a project name not in registry
- **WHEN** running `tasky project info nonexistent`
- **THEN** error message displayed with suggestion

---

### Requirement: Registry Performance

The registry SHALL perform efficiently for typical and large project counts.

#### Scenario: List responds quickly

- **GIVEN** a registry with 100 projects
- **WHEN** running `tasky project list`
- **THEN** response time is under 100ms

#### Scenario: Discovery scans efficiently

- **GIVEN** 1000 directories with 10 projects
- **WHEN** running `tasky project discover`
- **THEN** discovery completes in under 2 seconds

#### Scenario: Registry scales to hundreds

- **GIVEN** a registry with 500 projects
- **WHEN** running `tasky project list`
- **THEN** response time under 500ms and file size under 1MB

---

