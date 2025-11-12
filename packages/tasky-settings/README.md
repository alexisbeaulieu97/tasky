# tasky-settings

Configuration and settings management for Tasky with hierarchical configuration support.

## Overview

`tasky-settings` provides a type-safe, hierarchical configuration system for Tasky using Pydantic Settings. Configuration is loaded from multiple sources and merged with proper precedence rules.

## Features

- **Type-safe Settings**: Pydantic models with validation
- **Hierarchical Configuration**: Global → Project → Environment → CLI
- **TOML Configuration Files**: Human-friendly config format
- **Environment Variables**: Override settings via `TASKY_*` env vars
- **CLI Overrides**: Highest precedence for command-line flags

## Configuration Sources

Settings are loaded and merged in the following order (last wins):

1. **Model Defaults** (lowest precedence)
2. **Global Config**: `~/.tasky/config.toml`
3. **Project Config**: `.tasky/config.toml`
4. **Environment Variables**: `TASKY_*` with `__` for nesting
5. **CLI Overrides** (highest precedence)

## Usage

### Basic Usage

```python
from tasky_settings import get_settings

# Load settings from all sources
settings = get_settings()

# Access logging settings
print(settings.logging.verbosity)  # 0, 1, or 2
print(settings.logging.format)     # "standard", "json", or "minimal"

# Access task defaults
print(settings.task_defaults.priority)  # 1-5
print(settings.task_defaults.status)    # e.g., "pending"
```

### With CLI Overrides

```python
from tasky_settings import get_settings

# Override settings from CLI flags
cli_overrides = {
    "logging": {
        "verbosity": 2,
    }
}

settings = get_settings(cli_overrides=cli_overrides)
```

### With Explicit Project Root

```python
from pathlib import Path
from tasky_settings import get_settings

# Load project config from specific directory
settings = get_settings(project_root=Path("/path/to/project"))
```

## Configuration Files

### Global Configuration

Create `~/.tasky/config.toml` for user-wide defaults:

```toml
# Logging Configuration
[logging]
verbosity = 1  # 0=WARNING, 1=INFO, 2=DEBUG
format = "standard"  # "standard", "json", or "minimal"

# Task Defaults
[task_defaults]
priority = 3  # 1-5
status = "pending"
```

### Project Configuration

Create `.tasky/config.toml` in your project root to override global settings:

```toml
# Project-specific overrides
[logging]
verbosity = 2  # Debug logging for this project
format = "json"

[task_defaults]
priority = 5  # High priority project
```

## Environment Variables

Override any setting using environment variables with the `TASKY_` prefix and `__` for nesting:

```bash
# Override logging settings
export TASKY_LOGGING__VERBOSITY=2
export TASKY_LOGGING__FORMAT=json

# Override task defaults
export TASKY_TASK_DEFAULTS__PRIORITY=4
export TASKY_TASK_DEFAULTS__STATUS=active
```

## Settings Models

### LoggingSettings

```python
class LoggingSettings(BaseModel):
    verbosity: int = 0  # 0-2
    format: Literal["standard", "json", "minimal"] = "standard"
```

### TaskDefaultsSettings

```python
class TaskDefaultsSettings(BaseModel):
    priority: int = 3  # 1-5
    status: str = "pending"
```

### AppSettings

```python
class AppSettings(BaseSettings):
    logging: LoggingSettings
    task_defaults: TaskDefaultsSettings
```

## Precedence Examples

### Example 1: Project Overrides Global

**Global** (`~/.tasky/config.toml`):
```toml
[logging]
verbosity = 0
```

**Project** (`.tasky/config.toml`):
```toml
[logging]
verbosity = 2
```

**Result**: `verbosity = 2` (project wins)

### Example 2: Environment Overrides Files

**Project** (`.tasky/config.toml`):
```toml
[logging]
verbosity = 1
```

**Environment**:
```bash
export TASKY_LOGGING__VERBOSITY=2
```

**Result**: `verbosity = 2` (env var wins)

### Example 3: CLI Overrides Everything

**Project** (`.tasky/config.toml`):
```toml
[logging]
verbosity = 1
```

**Environment**:
```bash
export TASKY_LOGGING__VERBOSITY=2
```

**CLI**:
```python
settings = get_settings(cli_overrides={"logging": {"verbosity": 0}})
```

**Result**: `verbosity = 0` (CLI wins)

### Example 4: Partial Merging

**Global** (`~/.tasky/config.toml`):
```toml
[logging]
verbosity = 1
format = "standard"

[task_defaults]
priority = 3
status = "pending"
```

**Project** (`.tasky/config.toml`):
```toml
[logging]
verbosity = 2
```

**Result**:
- `logging.verbosity = 2` (from project)
- `logging.format = "standard"` (from global)
- `task_defaults.priority = 3` (from global)
- `task_defaults.status = "pending"` (from global)

## Validation

All settings are validated using Pydantic. Invalid values raise clear validation errors:

```python
# Invalid verbosity (must be 0-2)
config_file.write_text("[logging]\nverbosity = 5")
settings = get_settings()  # Raises ValidationError

# Invalid format (must be "standard", "json", or "minimal")
config_file.write_text('[logging]\nformat = "unknown"')
settings = get_settings()  # Raises ValidationError
```

## Testing

Settings can be easily tested with temporary configurations:

```python
import tempfile
from pathlib import Path
from tasky_settings import get_settings

def test_custom_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_dir = project_root / ".tasky"
        config_dir.mkdir()
        
        config_file = config_dir / "config.toml"
        config_file.write_text("[logging]\nverbosity = 2")
        
        settings = get_settings(project_root=project_root)
        assert settings.logging.verbosity == 2
```

## Architecture

- **models.py**: Pydantic settings models with validation
- **sources.py**: Custom settings sources for TOML files
- **__init__.py**: `get_settings()` factory with precedence logic

The settings system is designed to be:
- **Type-safe**: Full type hints and validation
- **Testable**: No global state, explicit dependencies
- **Extensible**: Easy to add new settings sections
- **Independent**: No runtime dependencies on other tasky packages

## See Also

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [TOML Specification](https://toml.io/)

