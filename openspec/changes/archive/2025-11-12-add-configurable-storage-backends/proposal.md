# Proposal: Configurable Storage Backends

**Status**: Draft  
**Created**: 2025-11-11  
**Change ID**: `add-configurable-storage-backends`

## Summary

Eliminate hardcoded backend dependencies in the CLI layer by extending the hierarchical configuration system (from `add-hierarchical-configuration`) to support storage backend selection and configuration. Enable users to choose different storage backends (JSON, SQLite, Postgres, etc.) through `.tasky/config.toml`, with automatic factory-based instantiation and dependency injection.

## Why

Currently, CLI commands directly instantiate `JsonTaskRepository` with hardcoded paths, creating tight coupling between presentation and infrastructure. The `add-hierarchical-configuration` change established `AppSettings` and TOML configuration—this change extends that foundation to storage backend selection.

**Problems this solves:**
- Users cannot choose SQLite or Postgres backends
- CLI commands manually instantiate repositories instead of using configuration
- Adding new backends requires modifying CLI code
- Testing requires swapping backend implementations

**Proposed solution:**
- Extend `AppSettings` with `StorageSettings` for backend selection
- Create `BackendRegistry` for plugin-style backend registration
- Add `create_task_service()` factory that reads config and instantiates backends
- Refactor CLI to use dependency injection

This enables plugin-like backend architecture without modifying higher layers.

## What Changes

### New Capabilities Added

1. **`storage-configuration`** - `StorageSettings` Pydantic model in `AppSettings`
   - Fields: `backend: str = "json"`, `path: str = "tasks.json"`
   - Loaded from `[storage]` section in `.tasky/config.toml`
   - Respects hierarchical precedence (CLI overrides → env vars → project config → global config → defaults)

2. **`backend-registry`** - Plugin registry for storage backend factories
   - `BackendRegistry` class with `register(name, factory)` and `get(name)` methods
   - `BackendFactory` type alias: `Callable[[Path], TaskRepository]`
   - Global singleton `registry` instance exported from `tasky-settings`
   - Self-registration at module load (backends register themselves in their `__init__.py`)

3. **`task-service-factory`** - Configuration-driven service instantiation
   - `find_project_root(start_path)` - Walks up directory tree to find `.tasky/` directory
   - `create_task_service(project_root)` - Loads settings, gets backend from registry, instantiates service
   - `ProjectNotFoundError` - Raised when no `.tasky/` directory found
   - Automatic path resolution relative to `.tasky/` directory

### Modified Capabilities

1. **`project-management`** commands
   - `tasky project init` now accepts `--backend` / `-b` option
   - Validates backend is registered before creating project
   - Persists backend choice to `.tasky/config.toml` in `[storage]` section
   - `tasky project info` now displays storage configuration from AppSettings

2. **`task-cli-operations`** commands
   - Refactored to use `create_task_service()` instead of direct repository instantiation
   - All task commands now work with configurable backends
   - Graceful error handling when project not found or backend invalid

### Files Changed

**New Files:**
- `packages/tasky-settings/src/tasky_settings/backend_registry.py` - BackendRegistry class
- `packages/tasky-settings/src/tasky_settings/factory.py` - Service factory and project discovery
- `packages/tasky-settings/tests/test_registry.py` - Registry tests
- `packages/tasky-settings/tests/test_factory.py` - Factory and project discovery tests

**Modified Files:**
- `packages/tasky-settings/src/tasky_settings/models.py` - Added `StorageSettings` to `AppSettings`
- `packages/tasky-settings/src/tasky_settings/__init__.py` - Export new classes and functions
- `packages/tasky-cli/src/tasky_cli/commands/projects.py` - Refactored to use TOML config with `[storage]` section
- `packages/tasky-cli/src/tasky_cli/commands/tasks.py` - Refactored to use factory
- `packages/tasky-cli/pyproject.toml` - Added `tomli_w>=1.0.0` dependency for TOML writing
- `packages/tasky-storage/src/tasky_storage/__init__.py` - Self-register JSON backend with registry

**Configuration Format:**
- All config in single `.tasky/config.toml` file (TOML format)
- New `[storage]` section stores backend selection and path
- Integrates with existing hierarchical configuration from `add-hierarchical-configuration`

### Backward Compatibility

- ✅ Projects without `.tasky/config.toml` work with defaults (backend="json", path="tasks.json")
- ✅ Existing `tasks.json` files continue to work (no data migration needed)
- ✅ Subdirectories can find parent project (project root discovery walks up tree)

## Goals

1. **Storage Configuration in AppSettings**: Extend `AppSettings` with `StorageSettings` model (backend type, path, options)
2. **Backend Registry**: Create a plugin-style registry mapping backend names to factory functions
3. **Service Factory**: Implement `create_task_service()` that reads `settings.storage` and instantiates the correct backend
4. **CLI Refactoring**: Update all commands to use factory and accept settings via dependency injection
5. **Default Backend**: Use JSON storage at `.tasky/tasks.json` when no config exists (backward compatibility)

## Non-Goals

- Implementing SQLite or Postgres backends (future work)
- Migration tools between backends
- Multi-backend support (single backend per project)
- Configuration UI (CLI flags only)

## Affected Capabilities

### New Capabilities

1. **`storage-configuration`**: `StorageSettings` model in `AppSettings` for backend selection
2. **`backend-registry`**: Plugin registry mapping backend names to factory functions
3. **`backend-self-registration`**: JSON backend automatically registers itself on module import
4. **`task-service-factory`**: `create_task_service()` that reads config and wires backends
5. **`project-cli-operations`**: `tasky project init/info` commands with backend selection and TOML config
6. **`task-cli-operations`**: Task commands using factory with dependency injection

### Modified Capabilities

1. **`hierarchical-settings`** (from `add-hierarchical-configuration`): Extend `AppSettings` with `storage` section
2. **`json-storage-backend`** (from `tasky-storage`): Add `from_path()` factory method for backend registration

## Architecture Changes

### Current Architecture (Manual Instantiation)

```
.tasky/config.toml → AppSettings (logging, task_defaults)
                         ↓
                    CLI commands
                         ↓
                    _create_task_service() (ad-hoc)
                         ↓
                    JsonTaskRepository (hardcoded)
```

**Problems:**
- Settings loaded but not used for storage configuration
- Manual instantiation in each command
- No factory pattern or dependency injection
- Cannot swap backends without modifying CLI code

### Proposed Architecture (Configuration-Driven)

```
.tasky/config.toml → AppSettings (logging, task_defaults, storage)
       ↓                               ↓
       │                          BackendRegistry
       │                               ↓
       └─→ create_task_service() → Instantiate backend
           (from tasky-settings)      ↓
                                   TaskService
                                       ↓
                                   CLI commands
```

**Benefits:**
- Storage configuration managed by settings system
- Factory-based instantiation with backend registry
- Dependency injection throughout CLI
- Plugin architecture for new backends

### Package Structure

**No new packages needed.** Extend existing packages:

```
packages/
├── tasky-settings/        # MODIFIED: Extend AppSettings
│   ├── models.py         # + StorageSettings model
│   ├── registry.py       # NEW: BackendRegistry
│   └── factory.py        # NEW: create_task_service()
│
├── tasky-storage/        # MODIFIED: Self-registers backends
│   └── __init__.py       # + registry.register("json", ...)
│
└── tasky-cli/            # MODIFIED: Use factory + DI
    ├── __init__.py       # Pass settings to commands
    ├── commands/tasks.py # Use create_task_service(settings)
    └── commands/projects.py # --backend flag support
```

## Configuration Schema

**File**: `.tasky/config.toml` (managed by hierarchical settings system)

Extends the existing config file with a `[storage]` section:

```toml
# Logging settings (from add-hierarchical-configuration)
[logging]
verbosity = 1
format = "standard"

# Task defaults (from add-hierarchical-configuration)
[task_defaults]
priority = 3
status = "pending"

# Storage configuration (NEW - this change)
[storage]
backend = "json"
path = "tasks.json"
# Backend-specific options (optional)
# [storage.options]
# wal_mode = true  # Example for SQLite backend
```

### Storage Section Fields

- `backend` (string, required): Backend name (e.g., "json", "sqlite", "postgres") - must be registered in `BackendRegistry`
- `path` (string, optional): Relative path from `.tasky/` directory; defaults to `tasks.json` for JSON backend
- `options` (object, optional): Backend-specific configuration (e.g., SQLite WAL mode, Postgres connection pool size)

## Key Design Decisions

### 1. Registry Pattern Over Service Locator

**Choice**: Use explicit `BackendRegistry` with `register(name, factory)` API  
**Rationale**: Makes dependencies visible, supports testing with mock registries  
**Alternative Rejected**: Service locator with hidden global state

### 2. Self-Registration at Module Load

**Choice**: Backends call `registry.register()` in their `__init__.py`  
**Rationale**: Zero-boilerplate addition of new backends  
**Trade-off**: Import-time side effects (acceptable for application code)

### 3. Factory Returns Configured Service

**Choice**: `create_task_service()` returns ready-to-use `TaskService`  
**Rationale**: CLI layer doesn't need to know about repositories or storage paths  
**Alternative Rejected**: Return repository and let CLI construct service

### 4. Extend Existing Settings Rather Than New Config File

**Choice**: Add `StorageSettings` to existing `AppSettings` model, reuse `.tasky/config.toml`
**Rationale**: Single source of truth, consistent schema, leverages existing hierarchy
**Alternative Rejected**: Create separate storage config file (duplication and confusion)

## Implementation Phases

### Phase 1: Storage Settings Model (tasky-settings)
- Create `StorageSettings` Pydantic model with `backend`, `path`, and `options` fields
- Add defaults (backend="json", path="tasks.json")
- Add validation for backend names and paths
- Extend `AppSettings` to include `storage: StorageSettings` field
- **Deliverable**: Type-safe storage configuration in AppSettings

### Phase 2: Backend Registry (tasky-settings)
- Create `BackendRegistry` class with `register(name: str, factory: Callable)` method
- Create `get_task_repository_factory(backend_name: str)` lookup method
- Add proper error handling for unregistered backends with helpful error messages
- **Deliverable**: Extensible backend registration system

### Phase 3: Service Factory (tasky-settings)
- Create `create_task_service(settings: AppSettings) -> TaskService` factory function
- Handle repository instantiation based on `settings.storage.backend`
- Resolve storage path relative to `.tasky/` directory
- Add clear error messages for missing or invalid backends
- **Deliverable**: Configurable service instantiation

### Phase 4: JSON Backend Registration (tasky-storage)
- Update `tasky-storage/__init__.py` to register JSON backend with BackendRegistry
- No changes needed to `JsonTaskRepository` (already has `from_path()`)
- **Deliverable**: JSON backend integrated with registry

### Phase 5: CLI Refactoring (tasky-cli)
- Update `tasky-cli/__init__.py` to pass settings to commands via context
- Refactor all task commands to accept settings and use `create_task_service()`
- Update `project init` to accept `--backend` flag and persist to config file
- Add `project config show` command to display storage configuration
- Remove ad-hoc `_create_task_service()` and `_storage_path()` functions
- **Deliverable**: Fully functional configuration-driven CLI with dependency injection

### Phase 6: Testing and Documentation
- Add unit tests for `StorageSettings` model and validation
- Add tests for `BackendRegistry` registration and lookup
- Add tests for `create_task_service()` factory with different backends
- Add integration tests for CLI with storage configuration
- Update README with configuration examples and backend selection guide
- **Deliverable**: Complete test coverage and documentation

## Success Criteria

1. ✅ Running `tasky project init --backend json` creates `.tasky/config.toml` with `[storage]` section
2. ✅ Running `tasky project config show` displays storage configuration
3. ✅ All task commands work without hardcoded `JsonTaskRepository` instantiation
4. ✅ Different backends can be swapped by changing `storage.backend` in config
5. ✅ Adding a new backend requires only registering it in registry (no CLI changes)
6. ✅ Running task commands without `project init` uses default JSON backend at `.tasky/tasks.json`
7. ✅ `StorageSettings` validates backend names and file paths
8. ✅ Tests cover settings model, registry, and factory with various backend scenarios

## Migration Path

### For Users
- **Existing projects** (no `.tasky/config.toml`): Continue to work with defaults (JSON backend, `.tasky/tasks.json`)
- **Opting in**: Create/update `.tasky/config.toml` with `[storage]` section to customize backend or path
- **New projects**: Running `tasky project init` creates config with `[storage]` section
- **No data migration**: Existing `tasks.json` files work as-is; no data movement needed when changing config

### For Developers
- **No breaking changes**: Existing code continues to work (defaults apply)
- **New pattern**: Use `create_task_service(settings)` instead of manual instantiation
- **Backend extension**: New backends register themselves in `tasky-storage/__init__.py` (no CLI changes needed)
- **Testing**: Use `BackendRegistry` to mock backends in tests

## Dependencies

### Package Dependencies

**No new package dependencies.** Uses existing:

```toml
# tasky-settings (already depends on: pydantic, pydantic-settings)
# No new dependencies needed

# tasky-storage (already depends on: tasky-tasks)
# No new dependencies needed

# tasky-cli (already depends on: typer, tasky-settings)
# No new dependencies needed
```

### Implementation Dependencies

- Phase 1 has no dependencies (standalone model)
- Phase 2 depends on Phase 1 (needs `StorageSettings`)
- Phase 3 depends on Phase 2 (needs `BackendRegistry`)
- Phase 4 depends on Phase 2 (needs to register with registry)
- Phase 5 depends on Phase 2 and 3 (needs factory)
- Phase 6 can run in parallel with Phase 5

## Risks and Mitigations

### Risk: Import Cycles
**Scenario**: `tasky-storage` imports `tasky-settings` to register with BackendRegistry
**Mitigation**: Use optional import in try-except block; registration is best-effort (tests can manually register)

### Risk: Backward Compatibility
**Scenario**: Existing projects with no config file or using default paths
**Mitigation**: `StorageSettings` has sensible defaults (backend="json", path="tasks.json"); no config required

### Risk: Invalid Backend Names
**Scenario**: Config specifies unregistered backend name
**Mitigation**: `create_task_service()` validates and provides clear error with list of available backends

### Risk: Config File Corruption or Missing Storage Section
**Scenario**: Malformed TOML or missing `[storage]` section
**Mitigation**: Pydantic validation with defaults; missing section uses defaults (backend="json", path="tasks.json")

### Risk: Path Resolution Issues
**Scenario**: Relative paths in config not resolved correctly
**Mitigation**: Always resolve relative to `.tasky/` directory explicitly; tests verify path resolution

## Open Questions

1. **Storage path precedence**: If config specifies a path, should CLI flags override it?
   - **Recommendation**: Config paths are "soft defaults"; future work could add `--storage-path` CLI override

2. **Backend-specific CLI flags**: Should `tasky project init` support backend-specific options?
   - **Recommendation**: MVP supports `--backend` only; backend-specific options go in config file

3. **Config migration**: When users upgrade and add storage config, should we provide a migration command?
   - **Recommendation**: Not needed for MVP (config is optional with sensible defaults)

## Coordination Notes

### Relationship to `add-hierarchical-configuration`

This change depends on `add-hierarchical-configuration` being complete:

- ✅ `add-hierarchical-configuration` created `AppSettings` model
- ✅ `add-hierarchical-configuration` created settings hierarchy (global → project → runtime)
- ✅ `add-hierarchical-configuration` implemented `.tasky/config.toml` loading via custom sources

**This change extends that foundation:**
- Adds `StorageSettings` model to `AppSettings`
- Uses existing hierarchy and TOML parsing (no duplication)
- Reuses settings loading infrastructure

**No conflicts:** Both changes cooperatively extend `AppSettings` without stepping on each other.

## References

- [VISION.md - User Story 2](../../../VISION.md#user-story-2-configurable-storage-backends)
- [AGENTS.md - Architecture Notes](../../../AGENTS.md)
- [add-hierarchical-configuration](../add-hierarchical-configuration/proposal.md) - Parent proposal
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Approval

- [ ] Architecture Review
- [ ] Coordination with `add-hierarchical-configuration` confirmed
- [ ] Ready for Implementation

---

**Next Steps**: Create spec deltas for storage-configuration, backend-registry, and task-service-factory capabilities, then draft `tasks.md`
