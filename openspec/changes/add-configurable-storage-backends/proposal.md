# Proposal: Configurable Storage Backends

**Status**: Draft  
**Created**: 2025-11-11  
**Change ID**: `add-configurable-storage-backends`

## Summary

Enable users to choose and configure different storage backends (JSON, SQLite, Postgres, etc.) for task persistence through a project configuration system, eliminating hardcoded backend dependencies in the CLI layer.

## Why

Currently, the CLI commands directly instantiate `JsonTaskRepository`, creating tight coupling between presentation and infrastructure layers. This violates Clean Architecture principles and prevents:

1. **Backend flexibility**: Users cannot choose SQLite for larger projects or Postgres for production
2. **Configuration persistence**: No way to store project-level settings (backend choice, paths, etc.)
3. **Extensibility**: Adding new backends requires modifying CLI code
4. **Testing**: Difficult to swap backends for integration testing

The proposed configuration system provides a clean separation of concerns where:
- Domain packages define repository protocols
- Infrastructure packages implement and self-register backends
- Settings package wires everything based on user configuration
- CLI layer remains pure, unaware of concrete backends

This enables a plugin-like architecture where backends can be added or swapped without touching higher layers.

## Goals

1. **Project Configuration**: Introduce `.tasky/config.json` to store backend selection and settings
2. **Backend Registry**: Create a plugin-style registry where backends self-register
3. **Service Factory**: Implement `create_task_service()` that reads config and wires the appropriate backend
4. **CLI Refactoring**: Update all commands to use the factory instead of direct instantiation
5. **Default Backend**: Use JSON storage when no config exists (backward compatibility)

## Non-Goals

- Implementing SQLite or Postgres backends (future work)
- Migration tools between backends
- Multi-backend support (single backend per project)
- Configuration UI (CLI flags only)

## Affected Capabilities

### New Capabilities

1. **`project-configuration`**: Models and persistence for `.tasky/config.json`
2. **`backend-registry`**: Plugin registry for storage backend factories
3. **`service-factory`**: Composition root that assembles `TaskService` from configuration

### Modified Capabilities

1. **`project-management`**: `project init` accepts `--backend` option and creates config file
2. **`task-cli-operations`**: All task commands use service factory instead of direct instantiation

## Architecture Changes

### Current Architecture (Tightly Coupled)

```
CLI → JsonTaskRepository (hardcoded)
```

### Proposed Architecture (Loosely Coupled)

```
CLI → create_task_service() → BackendRegistry → Configured Backend
      ↓
      ProjectConfig (.tasky/config.json)
```

### Package Structure

```
packages/
├── tasky-projects/         # NEW: Domain models for project config
│   └── config.py          # ProjectConfig, StorageConfig
│
├── tasky-settings/        # NEW: Composition root
│   ├── backend_registry.py # BackendRegistry, registration API
│   └── factory.py         # create_task_service()
│
├── tasky-storage/         # MODIFIED: Self-registers backends
│   └── __init__.py        # registry.register("json", ...)
│
└── tasky-cli/             # MODIFIED: Uses factory
    ├── commands/projects.py # --backend flag, config creation
    └── commands/tasks.py    # Calls create_task_service()
```

## Configuration Schema

**File**: `.tasky/config.json`

```json
{
  "version": "1.0",
  "storage": {
    "backend": "json",
    "path": "tasks.json"
  },
  "created_at": "2025-11-11T10:00:00Z"
}
```

### Fields

- `version`: Config schema version for future migrations
- `storage.backend`: Backend name (must be registered in `BackendRegistry`)
- `storage.path`: Relative path from `.tasky/` directory
- `created_at`: ISO 8601 timestamp (UTC)

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

### 4. Fail-Fast on Missing Config

**Choice**: Raise `ProjectNotFoundError` if config is missing  
**Rationale**: Explicit initialization via `project init` improves UX  
**Alternative Rejected**: Auto-create config with defaults (implicit behavior)

## Implementation Phases

### Phase 1: Foundation (tasky-projects)
- Create `ProjectConfig` and `StorageConfig` Pydantic models
- Implement `from_file()` and `to_file()` methods
- Add validation for backend names and paths
- **Deliverable**: Package with config models and persistence

### Phase 2: Registry and Factory (tasky-settings)
- Implement `BackendRegistry` with `register()` and `get()` methods
- Create `create_task_service()` factory
- Add `ProjectNotFoundError` exception
- **Deliverable**: Composition root package

### Phase 3: Backend Registration (tasky-storage)
- Update `__init__.py` to register JSON backend
- Add `from_path()` class method to `JsonTaskRepository` (already exists)
- **Deliverable**: Self-registering JSON backend

### Phase 4: CLI Integration
- Update `project init` to accept `--backend` flag and create config
- Add `project info` command to display config
- Refactor all task commands to use `create_task_service()`
- Add error handling for `ProjectNotFoundError`
- **Deliverable**: Fully functional configuration-driven CLI

### Phase 5: Testing and Documentation
- Add tests for config loading/saving
- Add tests for registry and factory
- Add integration tests for CLI with config
- Update README with configuration examples
- **Deliverable**: Complete test coverage and documentation

## Success Criteria

1. ✅ Running `tasky project init --backend json` creates `.tasky/config.json`
2. ✅ Running `tasky project info` displays current configuration
3. ✅ All task commands work without knowing about `JsonTaskRepository`
4. ✅ Adding a new backend requires only registering it (no CLI changes)
5. ✅ Running task commands without `project init` shows helpful error message
6. ✅ Tests cover config validation, registry, and factory behavior

## Migration Path

### For Users
- **Existing projects** (no config): First task command will prompt to run `project init`
- **New projects**: Must run `project init` before task commands
- **No data migration**: Existing `tasks.json` files work as-is

### For Developers
- **No breaking changes**: Existing tests continue to work
- **New pattern**: Use `create_task_service()` in new code
- **Migration guide**: Document how to add new backends

## Dependencies

### Package Dependencies

```toml
# tasky-projects
dependencies = ["pydantic>=2.0.0"]

# tasky-settings
dependencies = ["tasky-tasks", "tasky-projects"]

# tasky-cli
dependencies = ["typer>=0.20.0", "tasky-settings", "tasky-projects"]

# tasky-storage
dependencies = ["tasky-tasks"]  # No circular dependency
```

### Implementation Dependencies

- Phase 2 depends on Phase 1 (needs `ProjectConfig`)
- Phase 3 depends on Phase 2 (needs `BackendRegistry`)
- Phase 4 depends on Phase 2 and 3 (needs factory and registered backend)
- Phase 5 can run in parallel with Phase 4

## Risks and Mitigations

### Risk: Import Cycles
**Scenario**: `tasky-storage` imports `tasky-settings` for registration  
**Mitigation**: Use try-except block; registration is optional for testing

### Risk: Backward Compatibility
**Scenario**: Existing `.tasky/tasks.json` files without config  
**Mitigation**: First task command prompts to run `project init`

### Risk: Invalid Backend Names
**Scenario**: Config specifies unregistered backend  
**Mitigation**: Factory validates and provides clear error with available backends

### Risk: Config File Corruption
**Scenario**: Malformed JSON or invalid schema  
**Mitigation**: Pydantic validation with helpful error messages

## Open Questions

1. **Default backend behavior**: Should we auto-create config with JSON backend on first run?  
   - **Recommendation**: No, require explicit `project init` for clarity

2. **Config location**: Should we support user-level config (`~/.tasky/config.json`)?  
   - **Recommendation**: Project-level only for MVP, add user config later

3. **Backend parameters**: How to support backend-specific options (e.g., SQLite WAL mode)?  
   - **Recommendation**: Use `storage.options: dict[str, Any]` for extensibility

4. **Multiple projects**: How to detect which project is active in nested directories?  
   - **Recommendation**: Walk up directory tree to find `.tasky/`, add later if needed

## References

- [VISION.md - User Story 2](../../../VISION.md#user-story-2-configurable-storage-backends)
- [AGENTS.md - Architecture Notes](../../../AGENTS.md)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Approval

- [ ] Architecture Review
- [ ] Security Review (if applicable)
- [ ] Performance Review (if applicable)
- [ ] Ready for Implementation

---

**Next Steps**: Review proposal, create spec deltas, draft `tasks.md`, and validate with `openspec validate add-configurable-storage-backends --strict`
