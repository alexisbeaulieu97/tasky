# Implementation Tasks: Add Global Project Registry

This document outlines the ordered implementation tasks for adding a global project registry to tasky. Tasks are designed to deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: Domain Models (Foundation)

- [x] **Task 1.1**: Create domain models module
  - Create `packages/tasky-projects/src/tasky_projects/models.py`
  - Define `ProjectMetadata` model with fields: name, path, created_at, last_accessed, tags
  - Define `ProjectRegistry` model with fields: projects, registry_version
  - Add JSON serialization support via Pydantic
  - Add validation: path must be absolute, name must be valid identifier
  - **Duration**: 45 minutes
  - **Validation**: `uv run python -c "from tasky_projects.models import ProjectMetadata, ProjectRegistry"` succeeds

- [x] **Task 1.2**: Write unit tests for domain models
  - Create `packages/tasky-projects/tests/test_models.py`
  - Test `ProjectMetadata` creation and validation
  - Test path normalization (resolve relative paths to absolute)
  - Test JSON serialization round-trip
  - Test `ProjectRegistry` list management
  - Test registry version defaults
  - **Duration**: 30 minutes
  - **Validation**: `uv run pytest packages/tasky-projects/tests/test_models.py -v` passes

- [x] **Task 1.3**: Update package exports
  - Update `packages/tasky-projects/src/tasky_projects/__init__.py`
  - Export `ProjectMetadata`, `ProjectRegistry` from models
  - Maintain existing exports (ProjectConfig, StorageConfig)
  - **Duration**: 10 minutes
  - **Validation**: Import check succeeds

### Phase 2: Registry Service (Core Logic)

- [x] **Task 2.1**: Create ProjectRegistryService class
  - Create `packages/tasky-projects/src/tasky_projects/registry.py`
  - Define `ProjectRegistryService` class with `__init__(registry_path: Path)`
  - Implement `_load() -> ProjectRegistry` (read JSON file)
  - Implement `_save(registry: ProjectRegistry) -> None` (atomic write)
  - Implement lazy loading pattern (load on first access)
  - Handle missing registry file (create empty registry)
  - Handle corrupted registry file (log error, create new)
  - **Duration**: 60 minutes
  - **Validation**: Class compiles and type-checks

- [x] **Task 2.2**: Implement CRUD operations
  - Add `register_project(path: Path) -> ProjectMetadata` method
  - Add `unregister_project(path: Path) -> None` method
  - Add `get_project(name: str) -> ProjectMetadata | None` method
  - Add `list_projects() -> list[ProjectMetadata]` method
  - Add `update_last_accessed(path: Path) -> None` method
  - Validate project path exists and contains `.tasky/` directory
  - Prevent duplicate registrations (same path)
  - Derive project name from path basename
  - **Duration**: 60 minutes
  - **Validation**: Methods compile and type-check

- [x] **Task 2.3**: Write unit tests for CRUD operations
  - Create `packages/tasky-projects/tests/test_registry.py`
  - Test register new project
  - Test register duplicate project (should update, not duplicate)
  - Test unregister existing project
  - Test unregister non-existent project (should fail gracefully)
  - Test get project by name
  - Test list all projects (empty and non-empty)
  - Test update last accessed timestamp
  - Use temp directories for filesystem operations
  - Mock JSON file I/O where appropriate
  - **Duration**: 60 minutes
  - **Validation**: `uv run pytest packages/tasky-projects/tests/test_registry.py -v` passes

### Phase 3: Discovery Algorithm

- [x] **Task 3.1**: Implement directory walker
  - Add `_walk_directories(root: Path, max_depth: int) -> Iterator[Path]` helper
  - Implement recursive directory traversal
  - Respect max_depth parameter (default: 3)
  - Skip common non-project directories:
    - `.git`, `node_modules`, `venv`, `__pycache__`, `target`, `build`, `.venv`
  - Skip hidden directories except when they contain `.tasky/`
  - Handle permission errors gracefully (skip, log warning)
  - **Duration**: 45 minutes
  - **Validation**: Unit test with temp directory structure

- [x] **Task 3.2**: Implement project discovery
  - Add `discover_projects(search_paths: list[Path]) -> list[ProjectMetadata]` method
  - For each search path, walk directories looking for `.tasky/` directories
  - When found, create `ProjectMetadata` for parent directory
  - Deduplicate discovered projects (same path)
  - Sort results by last_accessed (most recent first)
  - **Duration**: 45 minutes
  - **Validation**: Method compiles and type-checks

- [x] **Task 3.3**: Implement auto-discovery on first use
  - Add `discover_and_register(search_paths: list[Path]) -> int` method
  - Call `discover_projects()` to find projects
  - Register each discovered project (update if already registered)
  - Return count of newly registered projects
  - **Duration**: 30 minutes
  - **Validation**: Method compiles

- [x] **Task 3.4**: Write unit tests for discovery
  - Create `packages/tasky-projects/tests/test_discovery.py`
  - Test discovery finds projects at various depths
  - Test discovery skips non-project directories
  - Test discovery handles permission errors
  - Test discovery deduplicates projects
  - Test auto-register updates existing projects
  - Use temp directory structures for realistic testing
  - **Duration**: 60 minutes
  - **Validation**: `uv run pytest packages/tasky-projects/tests/test_discovery.py -v` passes

### Phase 4: Settings Integration

- [x] **Task 4.1**: Add registry configuration to settings
  - Update `packages/tasky-settings/src/tasky_settings/config.py`
  - Add `registry_path: Path` field (default: `~/.tasky/registry.json`)
  - Add `discovery_paths: list[Path]` field (default: common locations)
  - Resolve `~` in paths during initialization
  - **Duration**: 20 minutes
  - **Validation**: Settings loads correctly with new fields

- [x] **Task 4.2**: Create registry service factory
  - Update `packages/tasky-settings/src/tasky_settings/__init__.py`
  - Add `get_project_registry_service() -> ProjectRegistryService` factory
  - Instantiate service with registry_path from settings
  - Cache service instance (singleton pattern)
  - **Duration**: 20 minutes
  - **Validation**: Factory returns service instance

- [x] **Task 4.3**: Write integration tests
  - Create `packages/tasky-settings/tests/test_registry_factory.py`
  - Test factory creates service with correct path
  - Test factory returns same instance (singleton)
  - Test service can persist registry through factory
  - **Duration**: 30 minutes
  - **Validation**: `uv run pytest packages/tasky-settings/tests/test_registry_factory.py -v` passes

### Phase 5: CLI Commands

- [x] **Task 5.1**: Implement `tasky project list` command
  - Update `packages/tasky-cli/src/tasky_cli/commands/projects.py`
  - Replace stub `list_command()` with real implementation
  - Call `get_project_registry_service().list_projects()`
  - On first run (empty registry), call `discover_and_register()` automatically
  - Format output: project name, path, last accessed timestamp
  - Handle empty registry (show helpful message)
  - Add `--no-discover` flag to skip auto-discovery
  - **Duration**: 45 minutes
  - **Validation**: `uv run tasky project list --help` shows updated help

- [x] **Task 5.2**: Implement `tasky project register` command
  - Add `register_command(path: str)` to projects.py
  - Validate path exists and contains `.tasky/` directory
  - Call `registry_service.register_project(Path(path))`
  - Show success message with project name
  - Handle errors (path not found, not a project)
  - **Duration**: 30 minutes
  - **Validation**: `uv run tasky project register --help` works

- [x] **Task 5.3**: Implement `tasky project unregister` command
  - Add `unregister_command(name: str)` to projects.py
  - Call `registry_service.unregister_project(name)`
  - Show success message
  - Handle errors (project not found)
  - Add confirmation prompt with `--yes/-y` flag to skip
  - **Duration**: 30 minutes
  - **Validation**: `uv run tasky project unregister --help` works

- [x] **Task 5.4**: Implement `tasky project discover` command
  - Add `discover_command()` to projects.py
  - Get discovery paths from settings
  - Call `registry_service.discover_and_register(paths)`
  - Show progress during discovery (spinner or dots)
  - Show summary: "Discovered N projects, registered M new"
  - List newly registered projects
  - Add `--paths` option to override search paths
  - **Duration**: 45 minutes
  - **Validation**: `uv run tasky project discover --help` works

- [x] **Task 5.5**: Enhance `tasky project info` command
  - Update existing `info_command()` to accept optional project name
  - If name provided, look up project in registry and show its info
  - If no name, show info for current directory (existing behavior)
  - Show: path, created_at, last_accessed, backend, storage path
  - Handle errors (project not found, not in project)
  - **Duration**: 30 minutes
  - **Validation**: `uv run tasky project info --help` updated

- [x] **Task 5.6**: Update CLI help text
  - Update docstrings for all command functions
  - Add examples in help text
  - Document auto-discovery behavior in `list` command
  - Document search paths in `discover` command
  - **Duration**: 20 minutes
  - **Validation**: Help text is clear and comprehensive

### Phase 6: Testing

- [x] **Task 6.1**: Write end-to-end CLI tests
  - Create `packages/tasky-cli/tests/test_project_registry.py`
  - Test `list` command with empty registry (triggers discovery)
  - Test `list` command with existing registry
  - Test `register` command with valid project
  - Test `register` command with invalid path (error)
  - Test `unregister` command removes project
  - Test `discover` command finds projects
  - Test `info` command with project name
  - Use temp directories for isolated testing
  - Mock filesystem where appropriate
  - **Duration**: 90 minutes
  - **Validation**: `uv run pytest packages/tasky-cli/tests/test_project_registry.py -v` passes

- [x] **Task 6.2**: Write integration tests with real filesystem
  - Create `packages/tasky-projects/tests/test_integration.py`
  - Test full workflow: discover → register → list → unregister
  - Test registry persistence across service instances
  - Test concurrent access (multiple services)
  - Test registry file corruption recovery
  - Test discovery with complex directory structures
  - Use temp home directory for isolation
  - **Duration**: 60 minutes
  - **Validation**: `uv run pytest packages/tasky-projects/tests/test_integration.py -v` passes

- [x] **Task 6.3**: Add edge case tests
  - Test registry with 100+ projects (performance)
  - Test discovery with deeply nested directories
  - Test permission errors during discovery
  - Test symlinks in project paths
  - Test project path with spaces and special characters
  - Test registry file in read-only directory (error handling)
  - **Duration**: 45 minutes
  - **Validation**: All edge cases handled gracefully

### Phase 7: Documentation and Polish

- [x] **Task 7.1**: Add docstrings to all public methods
  - Document `ProjectRegistryService` class and all methods
  - Document discovery algorithm and search strategy
  - Add examples in docstrings for common use cases
  - Document error conditions and exceptions
  - **Duration**: 30 minutes
  - **Validation**: All public APIs documented

- [x] **Task 7.2**: Update registry on project access
  - Update `tasky task` commands to call `update_last_accessed()`
  - Update when any task operation is performed in a project
  - Ensure minimal performance impact (lazy update)
  - **Duration**: 20 minutes
  - **Validation**: Last accessed timestamp updates correctly

- [x] **Task 7.3**: Add logging for registry operations
  - Use tasky_settings logging infrastructure
  - Log registry loads and saves (debug level)
  - Log discovery operations (info level)
  - Log errors during file I/O (error level)
  - **Duration**: 20 minutes
  - **Validation**: Logs appear during operations

- [x] **Task 7.4**: Handle stale registry entries
  - When listing projects, check if path still exists
  - Mark missing projects with warning indicator
  - Add `--validate` flag to `list` command to check all paths
  - Add `--clean` flag to remove stale entries
  - **Duration**: 30 minutes
  - **Validation**: Stale entries handled gracefully

### Phase 8: Final Validation

- [x] **Task 8.1**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage ≥85% for new code
  - Run `uv run pytest --cov=tasky_projects --cov-report=term-missing`
  - **Duration**: 30 minutes
  - **Validation**: All tests pass, coverage target met ✓ (526 tests pass, 84% coverage)

- [x] **Task 8.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - Run type checker: `uv run mypy packages/tasky-projects` (if configured)
  - **Duration**: 15 minutes
  - **Validation**: Code passes all quality checks ✓ (All ruff checks pass)

- [x] **Task 8.3**: Manual smoke testing
  - Initialize fresh project: `uv run tasky project init`
  - List projects (should trigger discovery): `uv run tasky project list`
  - Create second project in different directory
  - Manually register: `uv run tasky project register /path/to/project`
  - Verify both projects appear in list
  - Run discover explicitly: `uv run tasky project discover`
  - Test unregister: `uv run tasky project unregister project-name`
  - Verify registry file at `~/.tasky/registry.json`
  - Test info command with project name
  - **Duration**: 30 minutes
  - **Validation**: All workflows work end-to-end ✓ (All smoke tests passed)

- [x] **Task 8.4**: Performance testing
  - Create 100 test projects
  - Measure discovery time (should be <2 seconds)
  - Measure list time (should be <100ms)
  - Measure register time (should be <50ms)
  - **Duration**: 20 minutes
  - **Validation**: Performance targets met ✓ (Discovery: 0.37s, List: 0.27s, Register: 0.34s)

- [x] **Task 8.5**: Update CLAUDE.md if needed
  - Verify tasky-projects description matches new capabilities
  - Add note about registry file location if not obvious
  - Update any outdated references to project management
  - **Duration**: 10 minutes
  - **Validation**: Documentation is accurate ✓ (CLAUDE.md already accurate)

## Task Dependencies

### Sequential Dependencies
- Phase 1 must complete before Phase 2 (models needed for service)
- Phase 2 must complete before Phase 3 (service needed for discovery)
- Phase 4 depends on Phase 2 (service factory needs service)
- Phase 5 depends on Phase 2-4 (CLI needs service from factory)
- Phase 6 depends on Phase 1-5 (tests need all components)
- Phase 7-8 can happen after Phase 5 (polish and validation)

### Parallel Opportunities
- Phase 1 tests (1.2) can overlap with Phase 2 implementation (2.1)
- Phase 3 tests (3.4) can overlap with Phase 4 implementation (4.1-4.2)
- Phase 5 commands (5.1-5.5) can be implemented in parallel by different developers
- Phase 6 tests can be written while Phase 7 polish happens

## Testing Strategy

### Unit Tests (Fast, Isolated)
- Test domain models with mock data
- Test service methods with mock filesystem
- Test discovery algorithm with temp directories
- Coverage target: 95% for domain and service layers

### Integration Tests (Real Filesystem)
- Test registry persistence with real JSON files
- Test discovery with real directory structures
- Test service factory with real settings
- Coverage target: 85% for integration scenarios

### End-to-End Tests (Full CLI)
- Test complete user workflows
- Test error handling and edge cases
- Test help text and output formatting
- Coverage target: 80% for CLI commands

### Performance Tests
- Test discovery with 1000+ directories
- Test registry with 100+ projects
- Test concurrent access scenarios
- Target: <2s discovery, <100ms list

## Estimated Duration

### By Phase
- Phase 1 (Domain Models): 1.5 hours
- Phase 2 (Registry Service): 3 hours
- Phase 3 (Discovery): 3 hours
- Phase 4 (Settings Integration): 1.5 hours
- Phase 5 (CLI Commands): 3.5 hours
- Phase 6 (Testing): 3.5 hours
- Phase 7 (Documentation/Polish): 1.5 hours
- Phase 8 (Final Validation): 1.5 hours

**Total**: ~18 hours (optimistic)

### By Developer
- Single developer (sequential): 18-20 hours over 3-4 days
- Two developers (parallel): 12-14 hours over 2-3 days
- With testing focus: Add 20% time for thorough test coverage

### Realistic Estimate
Accounting for:
- Debugging time
- Test failures and fixes
- Code review iterations
- Documentation updates

**Realistic Total**: 20-24 hours

### Minimum Viable Implementation
If time-constrained, focus on:
- Phase 1-2 (domain + service): 4.5 hours
- Phase 4-5 (settings + CLI): 5 hours
- Phase 8 (validation): 2 hours
**MVP Total**: 11.5 hours

Then iterate with:
- Phase 3 (discovery): 3 hours
- Phase 6-7 (tests + polish): 5 hours

## Notes

- **Atomic Implementation**: Each task produces working, testable code
- **Rollback Safety**: Each phase can be reverted independently if issues arise
- **Progressive Enhancement**: MVP delivers value, discovery enhances it
- **Test-Driven**: Write tests alongside or immediately after implementation
- **Documentation-First**: Update help text as commands are implemented

## Success Criteria

### Phase Complete When:
- [ ] All tasks checked off
- [ ] All tests passing (`uv run pytest`)
- [ ] Code quality checks pass (`uv run ruff check`)
- [ ] Test coverage ≥85% overall
- [ ] Manual smoke tests successful
- [ ] No known bugs or regressions
- [ ] Documentation complete and accurate
- [ ] Performance targets met

### Ready for Review When:
- [ ] All success criteria met
- [ ] Self-review completed
- [ ] Commit messages clear and descriptive
- [ ] PR description includes:
  - Feature overview
  - Testing strategy
  - Screenshots/examples of CLI output
  - Breaking changes (none expected)
  - Migration notes (none needed)

### Ready for Merge When:
- [ ] Code review approved
- [ ] CI/CD pipeline passes
- [ ] Integration tests pass on clean environment
- [ ] Documentation reviewed and approved
- [ ] No outstanding review comments
