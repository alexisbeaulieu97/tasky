# Implementation Tasks: Configurable Storage Backends

**Change ID**: `add-configurable-storage-backends`
**Status**: Completed

---

## Overview

This document tracks the implementation of configurable storage backends. The implementation integrates with the hierarchical configuration system from `add-hierarchical-configuration`, using a single `.tasky/config.toml` file (not JSON) for all configuration concerns.

**Key Architectural Decision**: Instead of creating a separate storage config system, this change extends the existing `AppSettings` model with a `StorageSettings` section. This achieves the "single source of truth" goal and leverages the existing hierarchical configuration infrastructure.

---

## Phase 1: Settings Model Extension (tasky-settings)

### Task 1.1: Create StorageSettings model in AppSettings
- [x] Edit `packages/tasky-settings/src/tasky_settings/models.py`
- [x] Create `StorageSettings` Pydantic model with fields:
  - `backend: str = "json"` - Backend type (json, sqlite, postgres, etc.)
  - `path: str = "tasks.json"` - Relative path from `.tasky/` directory
- [x] Add field validation for non-empty backend name
- [x] Extend `AppSettings` to include `storage: StorageSettings` field
- [x] Update `__all__` exports to include `StorageSettings`

**Validation**: `StorageSettings` can be instantiated with defaults and as part of `AppSettings`

---

### Task 1.2: Write tests for StorageSettings model
- [x] Create or update `packages/tasky-settings/tests/test_models.py`
- [x] Test default values: backend="json", path="tasks.json"
- [x] Test custom backend and path values
- [x] Test model validation (Pydantic raises errors for invalid types)
- [x] Test StorageSettings as nested model in AppSettings

**Validation**: Run `uv run pytest packages/tasky-settings/tests/test_models.py -v`

---

## Phase 2: Backend Registry (tasky-settings)

### Task 2.1: Create BackendRegistry class
- [x] Create `packages/tasky-settings/src/tasky_settings/backend_registry.py`
- [x] Define `BackendFactory` type alias: `Callable[[Path], TaskRepository]`
- [x] Implement `BackendRegistry` class with:
  - `__init__()` with `_backends: dict[str, BackendFactory]`
  - `register(name: str, factory: BackendFactory) -> None`
  - `get(name: str) -> BackendFactory` with KeyError for missing backends
  - `list_backends() -> list[str]` returning sorted backend names
- [x] Create global singleton: `registry = BackendRegistry()`
- [x] Export in `__init__.py`

**Validation**: Registry can register and retrieve backends

---

### Task 2.2: Write tests for BackendRegistry
- [x] Create `packages/tasky-settings/tests/test_registry.py`
- [x] Test register and retrieve backend
- [x] Test register multiple backends
- [x] Test register overwrites existing backend
- [x] Test `get()` raises KeyError with descriptive message for unregistered backend
- [x] Test `list_backends()` returns sorted names
- [x] Test `list_backends()` returns empty list when none registered
- [x] Test global registry singleton is accessible

**Validation**: Run `uv run pytest packages/tasky-settings/tests/test_registry.py -v`

---

## Phase 3: Project Root Discovery and Service Factory (tasky-settings)

### Task 3.1: Implement ProjectNotFoundError exception
- [x] Add `class ProjectNotFoundError(Exception)` in `packages/tasky-settings/src/tasky_settings/factory.py`
- [x] Include helpful message with start_path
- [x] Export in `__init__.py`

**Validation**: Exception imports and raises correctly

---

### Task 3.2: Implement find_project_root() helper
- [x] Create `packages/tasky-settings/src/tasky_settings/factory.py`
- [x] Implement `find_project_root(start_path: Path | None = None) -> Path`
- [x] Start from `start_path or Path.cwd()`
- [x] Resolve path and walk up directory tree using `[current, *current.parents]`
- [x] Return path when `.tasky/` directory exists
- [x] Raise `ProjectNotFoundError` with helpful message if not found
- [x] Support being called from nested subdirectories

**Validation**: Finds `.tasky/` in current dir and parent dirs

---

### Task 3.3: Implement create_task_service() factory
- [x] Implement `create_task_service(project_root: Path | None = None) -> TaskService`
- [x] Call `find_project_root()` if project_root is None
- [x] Verify `.tasky/` directory exists when project_root provided explicitly
- [x] Load settings with `get_settings(project_root=project_root)`
- [x] Get factory from registry: `registry.get(settings.storage.backend)`
- [x] Construct absolute storage path: `project_root / ".tasky" / settings.storage.path`
- [x] Create repository: `repository = factory(storage_path)`
- [x] Call `repository.initialize()`
- [x] Return `TaskService(repository=repository)`
- [x] Export in `__init__.py`
- [x] Use local import for `get_settings` to avoid circular dependency

**Validation**: Creates configured TaskService from settings

---

### Task 3.4: Write tests for service factory and project discovery
- [x] Create `packages/tasky-settings/tests/test_factory.py`
- [x] Test `find_project_root()` finds `.tasky` in current dir
- [x] Test `find_project_root()` walks up directory tree
- [x] Test `find_project_root()` raises ProjectNotFoundError when not found
- [x] Test `find_project_root()` defaults to current working directory
- [x] Test `create_task_service()` with explicit project_root
- [x] Test `create_task_service()` with no arguments (auto-discovery)
- [x] Test `create_task_service()` raises ProjectNotFoundError with invalid root
- [x] Test `create_task_service()` raises KeyError for unregistered backend
- [x] Test `create_task_service()` constructs absolute paths from relative config paths
- [x] Test `create_task_service()` calls `repository.initialize()`

**Validation**: Run `uv run pytest packages/tasky-settings/tests/test_factory.py -v`

---

## Phase 4: JSON Backend Self-Registration (tasky-storage)

### Task 4.1: Add from_path() factory method to JsonTaskRepository
- [x] Edit `packages/tasky-storage/src/tasky_storage/json_repository.py`
- [x] Verify `from_path()` classmethod exists
- [x] Create `JsonStorage(path=path)`
- [x] Create repository instance: `cls(storage=storage)`
- [x] Call `initialize()` to ensure storage is ready
- [x] Return repository

**Validation**: Can create JsonTaskRepository from path

---

### Task 4.2: Register JSON backend in tasky-storage
- [x] Edit `packages/tasky-storage/src/tasky_storage/__init__.py`
- [x] Add import: `from tasky_settings import registry`
- [x] Wrap in try-except to handle ImportError gracefully (optional registry)
- [x] Call `registry.register("json", JsonTaskRepository.from_path)` at module level
- [x] Add comment explaining import-time registration pattern

**Validation**: Importing tasky_storage registers "json" backend

---

### Task 4.3: Write tests for backend registration
- [x] Create or update `packages/tasky-storage/tests/test_json_repository.py`
- [x] Test `from_path()` creates valid repository
- [x] Test `from_path()` initializes storage
- [x] Test importing tasky_storage registers "json" backend
- [x] Test registration is idempotent

**Validation**: Run `uv run pytest packages/tasky-storage/tests/ -v`

---

## Phase 5: CLI Refactoring (tasky-cli)

### Task 5.1: Refactor project init command
- [x] Edit `packages/tasky-cli/src/tasky_cli/commands/projects.py`
- [x] Add imports: `tomllib`, `tomli_w`, `registry`, `get_settings`
- [x] Remove imports: `ProjectConfig`, `StorageConfig`
- [x] Add helper: `_load_toml_file(path: Path) -> dict`
- [x] Add helper: `_save_toml_file(path: Path, data: dict) -> None`
- [x] Update `init_command()`:
  - Accept `--backend` option with default "json"
  - Add `-b` short option
  - Validate backend exists with `registry.get(backend)` before proceeding
  - Load existing config (if any) or start fresh
  - Create/update `[storage]` section with backend and path
  - Save as TOML using `tomli_w`
  - Show helpful output with backend and storage info
- [x] Update `info_command()`:
  - Load settings with `get_settings()`
  - Display Location, Backend, and Storage path from AppSettings
  - Handle missing projects with helpful error message

**Validation**: Can run `tasky project init --backend json` and see TOML file created

---

### Task 5.2: Add tomli_w dependency
- [x] Edit `packages/tasky-cli/pyproject.toml`
- [x] Add `tomli_w>=1.0.0` to dependencies
- [x] Run `uv sync` to install

**Validation**: `tasky-cli` installs with tomli_w

---

### Task 5.3: Refactor task commands to use factory
- [x] Edit `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
- [x] Remove imports: direct repository instantiation patterns
- [x] Add imports: `create_task_service`, `ProjectNotFoundError`
- [x] Update all task commands to:
  - Call `service = create_task_service()`
  - Handle `ProjectNotFoundError` with user-friendly message
  - Handle `KeyError` for invalid backends
  - Use TaskService methods (not direct repository access)
- [x] Add error messages suggesting `tasky project init`

**Validation**: Task commands work after `project init` and fail gracefully without project

---

## Phase 6: Testing and Verification

### Task 6.1: Run full test suite
- [x] Run `uv run pytest` from workspace root
- [x] Verify all tests pass
- [x] Fix any broken tests from refactoring
- [x] Verify factory and registry tests all pass
- [x] Verify project command tests pass

**Validation**: `uv run pytest` shows all tests passing

---

### Task 6.2: Manual CLI testing
- [x] Create test directory
- [x] Run `tasky project init` and verify `.tasky/config.toml` created with correct format
- [x] Run `tasky project info` and verify output shows TOML-based settings
- [x] Run `tasky task create "Test" "Details"` with default backend
- [x] Run `tasky task list` and verify task appears
- [x] Test in directory without project (should show error)
- [x] Test with subdirectory (should find parent project)
- [x] Test `tasky project init --backend json` explicitly

**Validation**: All manual tests work as expected

---

### Task 6.3: Linting and formatting
- [x] Run `uv run ruff check --fix`
- [x] Fix any linting issues
- [x] Run `uv run ruff format`
- [x] Verify formatting is correct

**Validation**: Ruff passes with no errors or warnings

---

## Key Implementation Differences from Initial Proposal

### Config Format: TOML vs JSON

**Initial Proposal**: Separate `ProjectConfig` model stored as `.tasky/config.json`

**Actual Implementation**: Integrated `StorageSettings` into `AppSettings`, uses existing `.tasky/config.toml` from hierarchical configuration

**Why**: The `add-hierarchical-configuration` change established a single `AppSettings` model with TOML-based configuration. Rather than creating a separate JSON config file, this change extends that same TOML file by adding a `[storage]` section. This achieves:
- **Single source of truth**: All config in one TOML file
- **Hierarchical inheritance**: Storage settings benefit from global → project → runtime precedence
- **Consistency**: Same format and precedence system for all settings
- **Extensibility**: Easy to add more storage options (e.g., `storage.options` for backend-specific settings)

### Configuration Precedence

The storage backend selection follows the same hierarchical precedence as all other settings:

1. **CLI overrides** (passed to `get_settings(cli_overrides={...})`)
2. **Environment variables** (TASKY_STORAGE_BACKEND, TASKY_STORAGE_PATH)
3. **Project config** (`.tasky/config.toml`)
4. **Global config** (`~/.tasky/config.toml`)
5. **Model defaults** (backend="json", path="tasks.json")

---

## Summary

**Total Implementation Tasks**: 20+
**Phases Completed**: All 6 phases

**Final Validation Checklist**:
- [x] All tests passing (184+ tests)
- [x] Linting clean (ruff check passes)
- [x] Code formatted (ruff format applied)
- [x] Manual testing completed
- [x] Documentation in proposal.md reflects TOML implementation
- [x] CLI works end-to-end (init → info → task operations)
- [x] Factory pattern properly wires backend selection from config

**Ready to Ship**: Yes - all acceptance criteria met, tests passing, implementation complete
