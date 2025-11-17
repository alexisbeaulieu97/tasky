# ADR-003: Configuration Hierarchy and Settings Precedence

## Status
Accepted

## Context
The system needs flexible configuration that works across multiple scenarios:
- **CLI usage**: Users run commands in various directories, need project-specific and global settings
- **Testing**: Tests need isolated configuration without affecting global state
- **Multi-project workflows**: Users work with multiple tasky projects simultaneously

Configuration sources include:
1. Environment variables (`TASKY_*`)
2. Global config file (`~/.tasky/config.toml`)
3. Project config file (`.tasky/config.toml`)
4. Command-line arguments
5. Hard-coded defaults

Without a clear precedence strategy, configuration becomes unpredictable and debugging becomes difficult.

## Decision
We implement a **hierarchical configuration system with explicit precedence**:

**Precedence order (highest to lowest):**
1. **Command-line arguments** (highest priority) - explicit user intent
2. **Environment variables** (`TASKY_BACKEND_TYPE`, etc.) - deployment/CI overrides
3. **Project config** (`.tasky/config.toml`) - project-specific settings
4. **Global config** (`~/.tasky/config.toml`) - user preferences
5. **Hard-coded defaults** (lowest priority) - sensible fallbacks

**Configuration Loading:**
```python
# In tasky-settings/sources.py
def load_settings() -> AppSettings:
    # 1. Load defaults
    settings = AppSettings()
    
    # 2. Override with global config (if exists)
    global_config = Path.home() / ".tasky" / "config.toml"
    if global_config.exists():
        settings.update_from_file(global_config)
    
    # 3. Override with project config (if in project)
    project_config = find_project_config()
    if project_config:
        settings.update_from_file(project_config)
    
    # 4. Override with environment variables
    settings.update_from_env()
    
    # 5. Override with CLI args (handled by Typer)
    return settings
```

**Key Design Decisions:**
- Use `pydantic-settings` for automatic environment variable parsing
- Project discovery walks upward from current directory (`.tasky/` indicates project root)
- Global registry stored in `~/.tasky/registry.json` (separate from config)

## Consequences

### Positive
- **Predictable behavior**: Clear precedence order, no ambiguity
- **Flexible deployment**: Can override via env vars for CI/Docker
- **User-friendly**: Sensible defaults, minimal config required
- **Project isolation**: Each project can have different backend settings
- **Testing friendly**: Tests can override with env vars or config files

### Negative
- **Configuration complexity**: Multiple sources can be confusing for debugging
- **File system dependencies**: Config loading depends on directory structure
- **Implicit discovery**: Project config auto-discovered, may surprise users

## Alternatives Considered

### Alternative 1: Single Global Config Only
Store all configuration in `~/.tasky/config.toml`:

**Rejected because:**
- Can't have project-specific backends (JSON for personal, SQLite for work)
- Breaks project portability (can't commit config to git)
- Forces all projects to share same settings

### Alternative 2: Environment Variables Only
No config files, everything via `TASKY_*` env vars:

**Rejected because:**
- Poor user experience (long env var exports in shell config)
- Hard to manage multiple projects
- No project-level configuration

### Alternative 3: Explicit Config Paths Only
Require `--config path/to/config.toml` on every command:

**Rejected because:**
- Terrible UX: users have to specify config every time
- Doesn't support global user preferences
- Makes simple workflows unnecessarily verbose

### Alternative 4: Reverse Precedence (Global > Project)
Make global config override project config:

**Rejected because:**
- Violates principle of least surprise: project settings should win
- Breaks project isolation: can't ensure project-specific backends
- Users expect local config to override global defaults

## References
- `packages/tasky-settings/src/tasky_settings/sources.py` - Configuration loading logic
- `packages/tasky-projects/src/tasky_projects/config.py` - Project config model
- pydantic-settings documentation: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
