# Proposal: Add Global Project Registry

**Change ID**: `add-project-registry`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant
**Phase**: Phase 5 (Non-blocking enhancement)
**Estimated Duration**: 5-6 hours

## Overview

This proposal introduces a global project registry that enables `tasky` to discover and manage multiple projects from anywhere in the filesystem. Currently, `tasky project list` is a stub, and users must be in a project directory to use task commands. This change implements the complete "tasky-projects" vision: a domain package that manages project discovery, registration, metadata, and navigation.

## Problem Statement

Users cannot effectively work with multiple tasky projects because:

1. **No Project Discovery**: Users must manually remember where each project is located
2. **Limited Context Switching**: Must `cd` to each project directory before running commands
3. **No Project Overview**: Cannot see a list of all projects or their metadata
4. **Manual Registration Required**: No automatic discovery of existing `.tasky` directories

Real-world scenarios that are currently impossible:
- "Show me all my tasky projects"
- "Which project was I working on yesterday?"
- "List tasks from my 'website' project without leaving my current directory"
- "Find all projects in ~/workspace"

This limits tasky's usefulness for developers managing multiple codebases, making it feel like isolated silos rather than a cohesive task management system.

## What Changes

This change adds comprehensive project registry functionality:

- **New domain models**: `ProjectMetadata` and `ProjectRegistry` in `tasky-projects` package
- **New service**: `ProjectRegistryService` for CRUD operations and discovery
- **New persistence**: JSON registry at `~/.tasky/registry.json`
- **Enhanced CLI commands**:
  - `tasky project list` - Shows all registered projects (triggers auto-discovery on first use)
  - `tasky project register <path>` - Manually register a project
  - `tasky project unregister <name>` - Remove project from registry
  - `tasky project discover` - Explicit discovery scan
  - `tasky project info [name]` - Enhanced to support looking up projects by name
- **Discovery algorithm**: Scans common dev directories for `.tasky/` directories
- **Settings integration**: Registry path and discovery paths configurable

**No breaking changes** - All existing commands continue to work unchanged.

## Why

### User Value

**Multi-Project Workflow**: Developers typically work on 3-10 projects simultaneously. A global registry enables:
- Quick context switching without filesystem navigation
- Overview of all projects in one place
- Future capability: cross-project task queries ("show all pending tasks across projects")

**Automatic Discovery**: Manual project registration creates friction and gets out of sync with reality. Auto-discovery ensures:
- New projects are automatically registered when initialized
- Existing projects are found during first use
- Registry stays current with minimal user intervention

**Foundation for Future Features**: This registry enables:
- `tasky switch <project>` to change active project
- `tasky task list --project=website` to query specific projects
- `tasky stats` to show aggregate statistics across projects
- Project templates and cloning

### Technical Value

**Completes tasky-projects Domain**: This change fulfills the vision from CLAUDE.md:
> "tasky-projects: project/workspace domain concerns (registries, metadata, task collections)"

Currently, tasky-projects only contains configuration models. This adds:
- Domain models: `ProjectMetadata`, `ProjectRegistry`
- Services: `ProjectRegistryService` with CRUD operations
- Discovery logic: filesystem scanning algorithms
- Persistence: JSON storage at `~/.tasky/registry.json`

**Architecture Alignment**: Follows clean architecture patterns:
- Domain models publish schemas and business rules
- Services coordinate discovery and persistence
- Storage layer implements persistence adapter
- CLI consumes composed services from settings

## Impact

### Affected Specs
- **NEW**: `project-registry-capability` - Complete new capability for project management
- **MODIFIED**: `project-cli-operations` - Enhanced `list` and `info` commands, new `register`/`unregister`/`discover` commands

### Affected Code
- `packages/tasky-projects/src/tasky_projects/`:
  - NEW: `models.py` - Domain models
  - NEW: `registry.py` - Service and discovery logic
  - MODIFIED: `__init__.py` - Export new symbols
- `packages/tasky-settings/src/tasky_settings/`:
  - MODIFIED: `config.py` - Add registry configuration
  - MODIFIED: `__init__.py` - Add service factory
- `packages/tasky-cli/src/tasky_cli/commands/projects.py`:
  - MODIFIED: Replace stub implementations with real functionality
  - NEW: Add `register_command`, `unregister_command`, `discover_command`

### Affected Tests
- NEW: `packages/tasky-projects/tests/test_models.py`
- NEW: `packages/tasky-projects/tests/test_registry.py`
- NEW: `packages/tasky-projects/tests/test_discovery.py`
- NEW: `packages/tasky-projects/tests/test_integration.py`
- NEW: `packages/tasky-cli/tests/test_project_registry.py`
- NEW: `packages/tasky-settings/tests/test_registry_factory.py`

### User Impact
- **Positive**: Multi-project workflow becomes seamless
- **Positive**: Auto-discovery reduces manual setup
- **Neutral**: First `list` command may be slower (one-time discovery)
- **None**: No breaking changes, all existing workflows preserved

## Proposed Solution

### Architecture

Add four new components to `packages/tasky-projects`:

1. **Domain Models** (`models.py`)
   ```python
   class ProjectMetadata(BaseModel):
       name: str           # Derived from path basename
       path: Path          # Absolute path to .tasky directory's parent
       created_at: datetime
       last_accessed: datetime
       tags: list[str] = []  # Future enhancement

   class ProjectRegistry(BaseModel):
       projects: list[ProjectMetadata]
       registry_version: str = "1.0"
   ```

2. **Registry Service** (`registry.py`)
   ```python
   class ProjectRegistryService:
       def __init__(self, registry_path: Path)
       def load() -> ProjectRegistry
       def save(registry: ProjectRegistry) -> None
       def register_project(path: Path) -> ProjectMetadata
       def unregister_project(path: Path) -> None
       def get_project(name: str) -> ProjectMetadata | None
       def list_projects() -> list[ProjectMetadata]
       def discover_projects(search_paths: list[Path]) -> list[ProjectMetadata]
       def update_last_accessed(path: Path) -> None
   ```

3. **Discovery Algorithm** (in `registry.py`)
   - Scan upward from current directory until finding `.tasky/`
   - Scan common locations: `~`, `~/projects`, `~/workspace`, `~/dev`, `~/src`
   - Recursively search each location (max depth: 3 levels)
   - Skip hidden directories (except `.tasky` itself)
   - Auto-register discovered projects

4. **Persistence Adapter** (JSON storage)
   - File location: `~/.tasky/registry.json`
   - Format: Simple JSON array of project metadata objects
   - Atomic writes with temp file + rename
   - Lazy initialization (create on first use)

### User-Facing Changes

#### New Commands

```bash
# List all registered projects (auto-discovers on first use)
tasky project list
# Output:
# Projects:
#   website     ~/code/website         Last accessed: 2025-11-12 10:30
#   api         ~/work/api-server      Last accessed: 2025-11-11 15:45
#   scripts     ~/scripts              Last accessed: 2025-11-10 09:00

# Manually register a project
tasky project register /path/to/project
# Output: ✓ Project registered: project-name

# Auto-discover projects in common locations
tasky project discover
# Output:
# Discovered 3 projects:
#   ✓ website     ~/code/website
#   ✓ api         ~/work/api-server
#   ✓ scripts     ~/scripts

# Remove a project from registry (doesn't delete files)
tasky project unregister website
# Output: ✓ Project unregistered: website

# Show detailed info about current or specific project
tasky project info
tasky project info website
# Output:
# Project: website
#   Path: /home/user/code/website
#   Created: 2025-11-01 14:23
#   Last accessed: 2025-11-12 10:30
#   Backend: json
#   Storage: tasks.json
```

#### Modified Commands

```bash
# Existing command now auto-discovers on first use
tasky project list
# First run: "Discovering projects... Found 3 projects"
# Subsequent runs: Just lists projects
```

### Discovery Algorithm Details

**Search Strategy**:
1. Check current directory and walk upward until finding `.tasky/` or reaching filesystem root
2. Check standard development directories if configured:
   - `~/projects`
   - `~/workspace`
   - `~/dev`
   - `~/src`
   - `~/code`
3. For each location, recursively scan subdirectories (max depth: 3)
4. Skip directories: `node_modules`, `.git`, `venv`, `__pycache__`, `target`, `build`

**Auto-Discovery Trigger**:
- Run on first `tasky project list` if registry file doesn't exist
- Run explicitly with `tasky project discover`
- Not run on every command (would be too slow)

**Lazy Registration**:
- Projects aren't registered until discovered or explicitly registered
- First use of any project command triggers discovery if registry is empty
- Updates `last_accessed` timestamp automatically when project is used

### Data Format

**Registry File** (`~/.tasky/registry.json`):
```json
{
  "registry_version": "1.0",
  "projects": [
    {
      "name": "website",
      "path": "/home/user/code/website",
      "created_at": "2025-11-01T14:23:45Z",
      "last_accessed": "2025-11-12T10:30:12Z",
      "tags": []
    },
    {
      "name": "api-server",
      "path": "/home/user/work/api-server",
      "created_at": "2025-10-15T09:12:33Z",
      "last_accessed": "2025-11-11T15:45:22Z",
      "tags": []
    }
  ]
}
```

**Why JSON instead of TOML**:
- Simple array of objects (JSON excels at this)
- No nested configuration sections needed
- Consistency with existing task storage format
- Pydantic models serialize to JSON naturally
- TOML better for hierarchical config, not flat lists

## Acceptance Criteria

### Functional Requirements

1. **Registry Persistence**
   - Registry file created at `~/.tasky/registry.json` on first use
   - Projects can be registered, unregistered, and queried
   - Registry survives across sessions (not in-memory only)
   - Concurrent access is safe (atomic writes)

2. **Discovery Works**
   - `tasky project discover` finds all `.tasky` directories in search paths
   - Auto-discovery runs on first `tasky project list` if registry is empty
   - Discovery skips common non-project directories (node_modules, etc.)
   - Discovery respects max depth limit (3 levels)

3. **CLI Commands Function**
   - `tasky project list` shows all registered projects with metadata
   - `tasky project register <path>` manually adds projects
   - `tasky project unregister <name>` removes projects from registry
   - `tasky project discover` scans and registers found projects
   - `tasky project info` shows detailed project information

4. **Metadata Management**
   - Project name derived from path basename
   - `created_at` timestamp set when project first registered
   - `last_accessed` timestamp updated when project is used
   - Duplicate projects (same path) are prevented

5. **Error Handling**
   - Attempting to register non-existent path shows clear error
   - Attempting to register path without `.tasky/` shows clear error
   - Unregistering non-existent project shows clear error
   - Registry file corruption is detected and handled gracefully

### Non-Functional Requirements

6. **Performance**
   - Discovery scans 1000+ directories in <2 seconds
   - Registry loads in <100ms (lazy loading, not on every command)
   - No performance impact on task commands (registry not loaded unless needed)

7. **Testability**
   - Unit tests for ProjectRegistryService (100% coverage)
   - Integration tests with real filesystem and JSON storage
   - End-to-end CLI tests for all commands
   - Test discovery algorithm with various directory structures

8. **Documentation**
   - All commands documented in CLI help text
   - Discovery algorithm explained in docstrings
   - Examples provided for common workflows

## Non-Goals

This proposal explicitly does NOT include:

- **Project Switching**: `tasky switch <project>` to change active project (future Phase 6)
- **Cross-Project Queries**: `tasky task list --project=website` (future Phase 7)
- **Project Templates**: `tasky project create --template=python` (future Phase 8)
- **Project Tags/Filtering**: Beyond basic tag storage (future enhancement)
- **Remote Project Registry**: Syncing registry across machines (future enhancement)
- **Project Statistics**: Aggregate task counts, completion rates (future feature)
- **Project Archiving**: Moving old projects to archive (future feature)

These features depend on the registry existing and should be proposed separately.

## Dependencies

### Required (Blocking)

This change depends on:
- **Phase 4 Complete**: Especially Phase 4.4 (TOML alignment) because project init uses TOML
- `add-configurable-storage-backends` (archived): Registry needs to understand backend types
- `add-hierarchical-configuration` (archived): Settings system for registry path configuration

### Optional (Non-blocking)

Future enhancements that will build on this:
- Project switching commands
- Cross-project task queries
- Project templates and initialization
- Advanced project filtering and search

## Risks and Mitigations

### Risk: Discovery Performance on Large Filesystems

**Risk**: Scanning thousands of directories could be slow
**Likelihood**: Medium
**Impact**: High (poor user experience)

**Mitigation**:
1. Implement max depth limit (3 levels)
2. Skip common non-project directories (node_modules, .git, venv)
3. Make discovery opt-in after first run (not on every command)
4. Add `--no-discover` flag to skip auto-discovery
5. Consider background discovery in future if needed

### Risk: Registry File Corruption

**Risk**: Concurrent access or crashes could corrupt registry
**Likelihood**: Low
**Impact**: Medium (registry reset required)

**Mitigation**:
1. Atomic writes with temp file + rename
2. Validate JSON on load, recreate if invalid
3. Keep registry simple (no complex state)
4. Log registry operations for debugging
5. Easy recovery: delete file and re-discover

### Risk: Project Name Collisions

**Risk**: Two projects with same basename ("app") but different paths
**Likelihood**: Medium
**Impact**: Low (can use full path to disambiguate)

**Mitigation**:
1. Use full path as unique identifier internally
2. Show path in list output for disambiguation
3. Support path-based unregister if name is ambiguous
4. Future: Allow user-defined project names

### Risk: Stale Registry Entries

**Risk**: Projects deleted from filesystem but still in registry
**Likelihood**: High
**Impact**: Low (confusing but not breaking)

**Mitigation**:
1. Validate project path on access, mark as stale if missing
2. Add `--validate` flag to `tasky project list` to check all paths
3. Future: Auto-cleanup stale entries after N days
4. Show warning in list output for missing projects

## Alternatives Considered

### Alternative 1: Database Instead of JSON File

**Description**: Use SQLite for registry storage
**Pros**: Better concurrency, query capabilities
**Cons**: Overkill for simple list of projects, adds complexity
**Decision**: Rejected. JSON is sufficient for <1000 projects

### Alternative 2: Store Registry in Each Project

**Description**: No global registry; each project knows about others via config
**Pros**: No global state, more decentralized
**Cons**: Cannot list projects without visiting each one, circular dependencies
**Decision**: Rejected. Global registry is simpler and matches user mental model

### Alternative 3: Environment Variable for Registry Path

**Description**: Let users configure registry location via `TASKY_REGISTRY`
**Pros**: More flexible for advanced users
**Cons**: Splits registry across locations, confusing default behavior
**Decision**: Deferred. Start with `~/.tasky/registry.json`, add config later if needed

### Alternative 4: Continuous Auto-Discovery

**Description**: Run discovery on every command to stay current
**Pros**: Registry always up-to-date
**Cons**: Too slow, poor user experience
**Decision**: Rejected. Use lazy discovery + explicit refresh

## Implementation Notes

### Package Organization

Add to `packages/tasky-projects/src/tasky_projects/`:
- `models.py`: `ProjectMetadata`, `ProjectRegistry` domain models
- `registry.py`: `ProjectRegistryService` with CRUD and discovery
- Update `__init__.py`: Export new public symbols

Tests in `packages/tasky-projects/tests/`:
- `test_models.py`: Test domain model serialization and validation
- `test_registry.py`: Test service methods with mock filesystem
- `test_discovery.py`: Test discovery algorithm with temp directories

### Settings Integration

Update `packages/tasky-settings/src/tasky_settings/`:
- Add `registry_path: Path` to settings (default: `~/.tasky/registry.json`)
- Add factory method: `get_project_registry_service() -> ProjectRegistryService`
- Inject registry path from settings into service

### CLI Integration

Update `packages/tasky-cli/src/tasky_cli/commands/projects.py`:
- Replace stub `list_command()` with real implementation
- Add `register_command(path: str)` for manual registration
- Add `unregister_command(name: str)` for removal
- Add `discover_command()` for explicit discovery
- Enhance `info_command()` to support project name parameter

### Storage Considerations

**Atomic Writes**:
```python
def save(registry: ProjectRegistry) -> None:
    temp_path = registry_path.with_suffix('.tmp')
    with temp_path.open('w') as f:
        f.write(registry.model_dump_json(indent=2))
    temp_path.rename(registry_path)  # Atomic on POSIX
```

**Lazy Loading**:
```python
class ProjectRegistryService:
    _registry: ProjectRegistry | None = None

    def _ensure_loaded(self) -> None:
        if self._registry is None:
            self._registry = self._load_or_create()
```

### Testing Strategy

**Unit Tests** (fast, isolated):
- Test ProjectRegistryService methods with mock storage
- Test discovery algorithm with mock filesystem walker
- Test model serialization and validation

**Integration Tests** (real filesystem):
- Create temp `.tasky` directories
- Test discovery finds projects correctly
- Test registry persists to real JSON file
- Test concurrent access scenarios

**End-to-End Tests** (full CLI):
- Test `tasky project list` with real registry
- Test manual registration workflow
- Test discovery workflow
- Test error handling and edge cases

## Related Changes

### Enables Future Features

- **Phase 6**: Project switching (`tasky switch <project>`)
- **Phase 7**: Cross-project queries (`tasky task list --project=website`)
- **Phase 8**: Project templates (`tasky project create --template=python`)
- **Future**: Project statistics and analytics
- **Future**: Remote registry synchronization

### Builds on Previous Work

- Phase 4.4 (TOML alignment): Project config uses TOML format
- Configurable storage backends: Registry understands backend types
- Hierarchical settings: Registry path comes from settings system

## Success Metrics

### Immediate (Phase 5 Complete)

- [ ] All commands implemented and tested
- [ ] Discovery finds projects in <2 seconds
- [ ] Registry persists correctly across sessions
- [ ] Test coverage ≥85% for all new code
- [ ] CLI help text comprehensive and clear

### Medium-Term (1 month after release)

- [ ] Users report improved multi-project workflow
- [ ] No registry corruption bugs reported
- [ ] Discovery performance acceptable for typical setups
- [ ] Feature requests for project switching (validates value)

### Long-Term (3 months after release)

- [ ] Foundation enables Phase 6-8 features
- [ ] Registry scales to 100+ projects without issues
- [ ] Users adopt tasky for multi-project task management
- [ ] Positive feedback on project discovery UX

## Migration Path

### For Existing Users

**Before**: No registry exists, all users start fresh

**After**:
1. First run of `tasky project list` triggers auto-discovery
2. User sees: "Discovering projects... Found N projects"
3. Registry file created at `~/.tasky/registry.json`
4. Subsequent runs use cached registry

**No Breaking Changes**: All existing commands continue to work unchanged

### For New Users

1. Run `tasky project init` in first project (creates `.tasky/`)
2. Run `tasky project list` (triggers discovery, finds first project)
3. Expand to more projects naturally over time

## Documentation Updates

### CLI Help Text

Update help text for:
- `tasky project` group (overview of registry concept)
- `tasky project list` (explain discovery behavior)
- `tasky project register` (manual registration examples)
- `tasky project discover` (when to use explicit discovery)

### Code Documentation

- Docstrings for all public methods in `ProjectRegistryService`
- Explain discovery algorithm and search path logic
- Document registry file format and schema
- Examples in docstrings for common use cases

### Future: User Guide

After Phase 5 complete, consider adding user guide section:
- Multi-project workflow examples
- Customizing discovery search paths
- Troubleshooting registry issues
- Best practices for project organization

## Open Questions

None currently. This is a well-scoped feature with clear requirements.

If questions arise during implementation:
1. Should discovery be recursive beyond depth 3?
   - **Decision**: Start with depth 3, make configurable if needed
2. Should registry validate project paths on every access?
   - **Decision**: Validate on access, mark stale but don't auto-remove
3. Should we support project name aliases?
   - **Decision**: Defer to future enhancement based on user feedback
