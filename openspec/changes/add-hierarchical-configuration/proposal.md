# Proposal: Hierarchical Configuration System

**Status**: Draft
**Created**: 2025-11-11
**Change ID**: `add-hierarchical-configuration`

## Summary

Implement a hierarchical configuration system using pydantic-settings with custom sources that allows users to define settings at three levels (global → project → CLI) with proper precedence and type validation. This provides a foundation for managing application settings, logging configuration, task defaults, and future configuration needs.

## Why

The current logging implementation (from `add-pluggable-logging`) has CLI directly calling `configure_logging()`, which works but doesn't scale. As Tasky grows, we need:

1. **Persistent Configuration**: Users want to set default verbosity, log formats, task priorities, etc. without CLI flags every time
2. **Per-Project Settings**: Different projects have different needs (e.g., verbose logging in active projects, minimal in archived ones)
3. **Configuration Layering**: Global defaults overridden by project-specific settings, overridden by CLI flags
4. **Type Safety**: Validation that configuration values are correct before they're used
5. **Extensibility**: Easy to add new configuration options without refactoring

Currently:
- No way to persist logging verbosity preferences
- No project-specific settings
- Each subsystem manages its own configuration ad-hoc
- Settings aren't validated or typed

This change introduces a proper configuration architecture using pydantic-settings with custom file sources.

## Goals

1. **Three-Level Hierarchy**: `~/.tasky/config.toml` → `.tasky/config.toml` → CLI flags (last wins)
2. **Environment Variable Support**: `TASKY_LOGGING__VERBOSITY=2` works automatically
3. **Type-Safe Settings Models**: Pydantic validates all configuration
4. **Custom Sources**: File sources for global and project configs
5. **Subsystem Settings**: Structured settings for logging, tasks, future features
6. **Backward Compatible**: Existing code continues to work; settings are opt-in

## Non-Goals

- Configuration UI or web interface (CLI/files only)
- Migration tools between config formats
- Dynamic runtime config reloading
- Per-user settings (only global + project for now)
- Configuration versioning or schema migration (future work)

## Affected Capabilities

### New Capabilities

1. **`hierarchical-settings`**: Core pydantic-settings models and custom sources
2. **`global-configuration`**: Loading from `~/.tasky/config.toml`
3. **`project-configuration`**: Loading from `.tasky/config.toml` (coordinated with `add-configurable-storage-backends`)

### Modified Capabilities

1. **`logging-infrastructure`**: Logging now configured from settings instead of direct CLI calls
2. **`cli-global-options`**: CLI callback updated to use settings system

## Architecture Changes

### Current Architecture (Direct Configuration)

```
CLI --verbose flag → configure_logging(verbosity=2)
```

### Proposed Architecture (Settings-Driven)

```
~/.tasky/config.toml
    ↓
.tasky/config.toml
    ↓
TASKY_* env vars
    ↓
CLI flags
    ↓
pydantic-settings merges all
    ↓
AppSettings object
    ↓
configure_logging(settings.logging)
```

### Package Structure

```
packages/
├── tasky-settings/           # MODIFIED: Becomes full settings system
│   ├── models.py            # NEW: AppSettings, LoggingSettings, etc.
│   ├── sources.py           # NEW: Custom file sources for TOML configs
│   ├── __init__.py          # NEW: get_settings() factory
│   └── tests/
│       ├── test_models.py   # NEW: Test settings models
│       ├── test_sources.py  # NEW: Test custom sources
│       └── test_hierarchy.py # NEW: Test precedence rules
│
├── tasky-logging/           # MODIFIED: Uses settings
│   └── config.py            # configure_logging(settings: LoggingSettings)
│
└── tasky-cli/               # MODIFIED: Uses settings
    └── __init__.py          # Loads settings, configures subsystems
```

## Configuration Schema

### Global Config: `~/.tasky/config.toml`

```toml
# Logging defaults
[logging]
verbosity = 1          # 0=WARNING, 1=INFO, 2=DEBUG
format = "standard"    # "standard", "json", "minimal"

# Task defaults (for when tasks are created)
[task_defaults]
priority = 3           # 1-5
status = "pending"
```

### Project Config: `.tasky/config.toml`

```toml
# Project-specific overrides
[logging]
verbosity = 2          # This project wants debug logs

[task_defaults]
priority = 5           # High priority project
```

### Environment Variables

```bash
# Override any setting via env vars
export TASKY_LOGGING__VERBOSITY=2
export TASKY_LOGGING__FORMAT=json
export TASKY_TASK_DEFAULTS__PRIORITY=4
```

### CLI Flags

```bash
# Highest priority - overrides everything
tasky -vv task list    # verbosity=2 from CLI
```

## Key Design Decisions

### 1. Pydantic-Settings Over Custom Loader

**Choice**: Use pydantic-settings with custom sources
**Rationale**:
- Handles env vars automatically
- Type validation built-in
- Well-tested, maintained library
- Custom sources let us add file hierarchy

**Alternative Rejected**: Roll our own config loader (unnecessary complexity)

### 2. TOML Over JSON for Config Files

**Choice**: Use TOML format for human-editable configs
**Rationale**:
- More human-friendly (comments, cleaner syntax)
- Standard for Python projects (pyproject.toml)
- No security issues like YAML
- Good Python stdlib support (tomllib)

**Alternative Rejected**: JSON (less user-friendly), YAML (security concerns)

### 3. Custom Sources for File Loading

**Choice**: Implement `TomlConfigSource`, `GlobalConfigSource`, `ProjectConfigSource`
**Rationale**:
- Pydantic-settings designed for this pattern
- Each source is independent and testable
- Clear precedence order

**Alternative Rejected**: Manually merge configs (error-prone)

### 4. Settings as Dependency, Not Global

**Choice**: `get_settings()` returns settings object passed to subsystems
**Rationale**:
- Explicit dependencies (testable)
- No hidden global state
- Can reset for testing

**Alternative Rejected**: Singleton with global access (harder to test)

### 5. Logging Doesn't Depend on Settings Package

**Choice**: Logging takes `LoggingSettings` object as parameter (type-only import)
**Rationale**:
- Keeps logging independently usable
- No circular dependencies
- Settings depends on logging models, not vice versa

**Trade-off**: Slight duplication of models, but clean architecture

## Implementation Phases

### Phase 1: Settings Models (tasky-settings)
- Create `LoggingSettings`, `TaskDefaultsSettings`, `AppSettings` models
- Add proper field validation and defaults
- **Deliverable**: Type-safe settings models

### Phase 2: Custom Sources (tasky-settings)
- Implement `TomlConfigSource` base class
- Implement `GlobalConfigSource` for `~/.tasky/config.toml`
- Implement `ProjectConfigSource` for `.tasky/config.toml`
- **Deliverable**: File loading with precedence

### Phase 3: Settings Factory (tasky-settings)
- Implement `get_settings()` with custom sources
- Handle missing files gracefully
- Add proper error messages for invalid configs
- **Deliverable**: Working settings loader

### Phase 4: Logging Integration
- Update `configure_logging()` to accept `LoggingSettings`
- Update CLI callback to use settings system
- **Deliverable**: Logging configured from files/env/CLI

### Phase 5: Testing and Documentation
- Unit tests for models, sources, and factory
- Integration tests for hierarchy precedence
- Example config files in docs
- **Deliverable**: Full test coverage and documentation

## Success Criteria

1. ✅ Creating `~/.tasky/config.toml` with `logging.verbosity = 1` makes all commands use INFO logs by default
2. ✅ Creating `.tasky/config.toml` with different verbosity overrides global config
3. ✅ CLI `-v` flag overrides both file configs
4. ✅ `TASKY_LOGGING__VERBOSITY=2` environment variable overrides file configs but not CLI flags
5. ✅ Invalid config values raise helpful validation errors
6. ✅ Missing config files don't cause errors (use defaults)
7. ✅ Existing commands work without any config files (backward compatible)

## Migration Path

### For Users
- **No action required**: Existing workflows continue to work
- **Optional**: Create config files for persistent settings
- **Example**: Create `~/.tasky/config.toml` for your logging preferences

### For Developers
- **Existing code**: Continue to work (settings are opt-in)
- **New pattern**: Use `settings = get_settings()` and pass to subsystems
- **Logging**: Update to `configure_logging(settings.logging)`

## Coordination with Other Changes

### Relationship to `add-configurable-storage-backends`

**Status**: `add-configurable-storage-backends` is at 0/167 tasks (not started)

**Overlap**: Both want to create `.tasky/config.toml` for project configuration

**Resolution**:
1. **This change** creates the hierarchical settings infrastructure and focuses on:
   - Settings models and validation
   - File loading with precedence
   - Logging configuration
   - Task defaults

2. **Storage backends change** will later add:
   - `storage.backend` field to settings
   - `storage.path` field to settings
   - Backend registry integration

**Integration Path**:
- This change implements: `AppSettings` with `logging` and `task_defaults` sections
- Storage backends change adds: `storage` section to `AppSettings`
- Both use the same settings infrastructure

**Benefits**:
- Hierarchical config lands first (needed for logging)
- Storage backends change is simplified (settings already exist)
- No duplication of config loading logic

### Relationship to `add-pluggable-logging`

**Status**: `add-pluggable-logging` is complete (ready to merge)

**Modification**: This change retrofits logging to use settings:
- Logging package API stays the same
- CLI integration changes from direct call to settings-driven
- Adds ability to persist logging preferences in config files

## Dependencies

### Package Dependencies

```toml
# tasky-settings/pyproject.toml
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-settings>=2.5.0",
]

# tasky-logging/pyproject.toml
dependencies = []  # No dependency on settings (type-only if needed)

# tasky-cli/pyproject.toml
dependencies = [
    "typer>=0.20.0",
    "tasky-settings",  # NEW dependency
    "tasky-logging",
]
```

### Implementation Dependencies

- Phase 2 depends on Phase 1 (needs models)
- Phase 3 depends on Phase 2 (needs sources)
- Phase 4 depends on Phase 3 (needs factory)
- Phase 5 can run in parallel with Phase 4

## Risks and Mitigations

### Risk: Config File Location Discovery
**Scenario**: User runs `tasky` from subdirectory, which config applies?
**Mitigation**: For MVP, use `Path.cwd()` for project root. Future: walk up directory tree

### Risk: Config File Parsing Errors
**Scenario**: User creates invalid TOML or wrong structure
**Mitigation**: Pydantic validation with helpful error messages showing exactly what's wrong

### Risk: Breaking Existing Workflows
**Scenario**: Config changes break commands that worked before
**Mitigation**: All config is optional; missing files use sensible defaults

### Risk: Circular Dependencies
**Scenario**: Settings imports logging, logging imports settings
**Mitigation**: Logging uses TYPE_CHECKING for imports, no runtime dependency

## Open Questions

1. **Config file format**: Should we support JSON as alternative to TOML?
   - **Recommendation**: TOML only for MVP, JSON can be added via custom source later

2. **Config validation on save**: Should we provide `tasky config validate` command?
   - **Recommendation**: Yes, add in Phase 5 for better UX

3. **Config editing**: Should we provide `tasky config set logging.verbosity 2`?
   - **Recommendation**: Manual editing only for MVP, CLI commands later

4. **Default config generation**: Should `tasky init` create example config?
   - **Recommendation**: Yes, create `.tasky/config.toml` with comments explaining options

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [TOML Specification](https://toml.io/)
- CLAUDE.md - Repository architecture guidelines

## Approval

- [ ] Architecture Review
- [ ] Coordination with `add-configurable-storage-backends` approved
- [ ] Ready for Implementation

---

**Next Steps**: Create spec deltas, draft `tasks.md`, validate with `openspec validate add-hierarchical-configuration --strict`
