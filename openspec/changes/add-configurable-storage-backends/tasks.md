# Implementation Tasks: Configurable Storage Backends

**Change ID**: `add-configurable-storage-backends`  
**Status**: Not Started

---

## Phase 1: Foundation - Project Configuration (tasky-projects)

### Task 1.1: Create tasky-projects package structure
- [ ] Create `packages/tasky-projects/src/tasky_projects/` directory
- [ ] Create `packages/tasky-projects/src/tasky_projects/__init__.py` with exports
- [ ] Create `packages/tasky-projects/src/tasky_projects/py.typed` marker
- [ ] Create `packages/tasky-projects/tests/` directory
- [ ] Update `packages/tasky-projects/pyproject.toml` with dependencies

**Validation**: Package imports successfully

---

### Task 1.2: Implement ProjectConfig and StorageConfig models
- [ ] Create `packages/tasky-projects/src/tasky_projects/config.py`
- [ ] Define `StorageConfig` with `backend` and `path` fields
- [ ] Define `ProjectConfig` with `version`, `storage`, and `created_at` fields
- [ ] Set default values: backend="json", path="tasks.json", version="1.0"
- [ ] Use `datetime.now(tz=UTC)` for `created_at` default
- [ ] Export both classes in `__init__.py`

**Validation**: Can instantiate models with defaults

---

### Task 1.3: Implement ProjectConfig.from_file()
- [ ] Add `@classmethod from_file(cls, path: Path) -> "ProjectConfig"`
- [ ] Read JSON file and parse with `json.loads()`
- [ ] Use `cls.model_validate(data)` to create instance
- [ ] Raise `FileNotFoundError` with path if file doesn't exist
- [ ] Let Pydantic handle validation errors

**Validation**: Loads valid config files, rejects invalid ones

---

### Task 1.4: Implement ProjectConfig.to_file()
- [ ] Add `def to_file(self, path: Path) -> None`
- [ ] Create parent directories with `path.parent.mkdir(parents=True, exist_ok=True)`
- [ ] Serialize with `self.model_dump_json(indent=2)`
- [ ] Write to file with proper encoding

**Validation**: Saves config and can reload it identically

---

### Task 1.5: Write tests for project configuration
- [ ] Create `packages/tasky-projects/tests/test_config.py`
- [ ] Test default values for both models
- [ ] Test `from_file()` with valid config
- [ ] Test `from_file()` with missing file (FileNotFoundError)
- [ ] Test `from_file()` with invalid JSON (validation error)
- [ ] Test `to_file()` creates directories
- [ ] Test round-trip (save then load produces identical config)
- [ ] Test `created_at` uses UTC timezone

**Validation**: Run `uv run pytest packages/tasky-projects/tests/ -v`

---

## Phase 2: Registry and Factory (tasky-settings)

### Task 2.1: Create tasky-settings package structure
- [ ] Create `packages/tasky-settings/src/tasky_settings/` directory
- [ ] Create `packages/tasky-settings/src/tasky_settings/__init__.py`
- [ ] Create `packages/tasky-settings/src/tasky_settings/py.typed` marker
- [ ] Create `packages/tasky-settings/tests/` directory
- [ ] Update `packages/tasky-settings/pyproject.toml` with dependencies

**Validation**: Package imports successfully

---

### Task 2.2: Implement BackendRegistry
- [ ] Create `packages/tasky-settings/src/tasky_settings/backend_registry.py`
- [ ] Define `BackendFactory` type alias: `Callable[[Path], TaskRepository]`
- [ ] Implement `BackendRegistry.__init__()` with `_backends: dict`
- [ ] Implement `register(name: str, factory: BackendFactory)`
- [ ] Implement `get(name: str) -> BackendFactory` with KeyError for missing backends
- [ ] Implement `list_backends() -> list[str]` returning sorted names
- [ ] Create global singleton: `registry = BackendRegistry()`
- [ ] Export in `__init__.py`

**Validation**: Can register and retrieve backends

---

### Task 2.3: Write tests for BackendRegistry
- [ ] Create `packages/tasky-settings/tests/test_registry.py`
- [ ] Test register and retrieve backend
- [ ] Test register multiple backends
- [ ] Test overwrite existing backend
- [ ] Test get() raises KeyError with helpful message for unregistered backend
- [ ] Test list_backends() returns sorted names
- [ ] Test list_backends() returns empty list when none registered
- [ ] Test global registry singleton is accessible

**Validation**: Run `uv run pytest packages/tasky-settings/tests/test_registry.py -v`

---

### Task 2.4: Implement ProjectNotFoundError exception
- [ ] Add `class ProjectNotFoundError(Exception)` in `factory.py`
- [ ] Export in `__init__.py`

**Validation**: Exception can be imported

---

### Task 2.5: Implement find_project_root() helper
- [ ] Create `packages/tasky-settings/src/tasky_settings/factory.py`
- [ ] Implement `find_project_root(start_path: Path | None = None) -> Path`
- [ ] Start from `start_path or Path.cwd()`
- [ ] Walk up directory tree using `[current, *current.parents]`
- [ ] Return parent when `.tasky/config.json` exists
- [ ] Raise `ProjectNotFoundError` with helpful message if not found

**Validation**: Finds config in current dir and parent dirs

---

### Task 2.6: Implement create_task_service() factory
- [ ] Implement `create_task_service(project_root: Path | None = None) -> TaskService`
- [ ] Call `find_project_root()` if project_root is None
- [ ] Load config with `ProjectConfig.from_file(project_root / ".tasky/config.json")`
- [ ] Get factory from registry: `registry.get(config.storage.backend)`
- [ ] Construct absolute storage path: `project_root / ".tasky" / config.storage.path`
- [ ] Create repository: `repository = factory(storage_path)`
- [ ] Return `TaskService(repository=repository)`
- [ ] Export in `__init__.py`

**Validation**: Creates service from config file

---

### Task 2.7: Write tests for service factory
- [ ] Create `packages/tasky-settings/tests/test_factory.py`
- [ ] Test create_task_service() with explicit project_root
- [ ] Test create_task_service() with current directory
- [ ] Test find_project_root() walks up directory tree
- [ ] Test ProjectNotFoundError when no config found
- [ ] Test ProjectNotFoundError when .tasky exists but config missing
- [ ] Test KeyError for unregistered backend in config
- [ ] Test absolute path construction from relative path
- [ ] Test factory is called with correct storage path

**Validation**: Run `uv run pytest packages/tasky-settings/tests/test_factory.py -v`

---

## Phase 3: Backend Self-Registration (tasky-storage)

### Task 3.1: Add from_path() factory method to JsonTaskRepository
- [ ] Check if `from_path()` already exists in `JsonTaskRepository`
- [ ] If not, add `@classmethod from_path(cls, path: Path) -> "JsonTaskRepository"`
- [ ] Create `JsonStorage(path=path)`
- [ ] Create repository instance: `repository = cls(storage=storage)`
- [ ] Call `repository.initialize()` to ensure file exists
- [ ] Return repository

**Validation**: Can create repository from path

---

### Task 3.2: Register JSON backend in tasky-storage
- [ ] Edit `packages/tasky-storage/src/tasky_storage/__init__.py`
- [ ] Add import attempt: `from tasky_settings import registry`
- [ ] Wrap in try-except to handle ImportError gracefully
- [ ] Call `registry.register("json", JsonTaskRepository.from_path)`
- [ ] Add comment explaining import-time registration

**Validation**: Import tasky_storage registers "json" backend

---

### Task 3.3: Write tests for backend registration
- [ ] Create or update `packages/tasky-storage/tests/test_json_repository.py`
- [ ] Test `from_path()` creates valid repository
- [ ] Test `from_path()` initializes storage file
- [ ] Test importing tasky_storage registers "json" backend (integration test)
- [ ] Test registration is idempotent (multiple imports don't error)

**Validation**: Run `uv run pytest packages/tasky-storage/tests/ -v`

---

## Phase 4: CLI Integration

### Task 4.1: Refactor project init command
- [ ] Edit `packages/tasky-cli/src/tasky_cli/commands/projects.py`
- [ ] Add imports: `ProjectConfig`, `StorageConfig`, `registry`
- [ ] Add `--backend` option with default "json" to `init_command()`
- [ ] Add `-b` short option
- [ ] Validate backend exists with `registry.get(backend)` before creating config
- [ ] Create `ProjectConfig` with `StorageConfig(backend=backend, path="tasks.json")`
- [ ] Save config with `config.to_file(storage_root / "config.json")`
- [ ] Update output message to show backend
- [ ] Add warning when overwriting existing config

**Validation**: Can run `tasky project init --backend json`

---

### Task 4.2: Implement project info command
- [ ] Add `info_command()` to `projects.py`
- [ ] Load config with `ProjectConfig.from_file(Path(".tasky/config.json"))`
- [ ] Display: Location, Backend, Storage, Created timestamp
- [ ] Handle `FileNotFoundError` with helpful error message
- [ ] Suggest running `project init` in error message

**Validation**: Can run `tasky project info`

---

### Task 4.3: Refactor task list command
- [ ] Edit `packages/tasky-cli/src/tasky_cli/commands/tasks.py`
- [ ] Remove imports: `JsonTaskRepository`, `JsonStorage`, `Path`
- [ ] Add imports: `create_task_service`, `ProjectNotFoundError`
- [ ] Replace direct repository instantiation with `service = create_task_service()`
- [ ] Add try-except for `ProjectNotFoundError` with helpful message
- [ ] Add try-except for `KeyError` (invalid backend)

**Validation**: Can run `tasky task list` after project init

---

### Task 4.4: Refactor task create command
- [ ] Update `create_command()` in `tasks.py`
- [ ] Replace repository instantiation with `service = create_task_service()`
- [ ] Add error handling for `ProjectNotFoundError` and `KeyError`
- [ ] Keep rest of logic unchanged

**Validation**: Can create tasks via CLI

---

### Task 4.5: Create helper function for service creation
- [ ] Add `get_service()` helper function in `tasks.py`
- [ ] Wrap `create_task_service()` call
- [ ] Handle `ProjectNotFoundError` with user-friendly message
- [ ] Handle `KeyError` for invalid backends
- [ ] Exit with code 1 on errors
- [ ] Update all task commands to use helper

**Validation**: All task commands have consistent error handling

---

### Task 4.6: Update CLI dependencies
- [ ] Edit `packages/tasky-cli/pyproject.toml`
- [ ] Add `tasky-settings` to dependencies
- [ ] Add `tasky-projects` to dependencies
- [ ] Remove direct dependency on `tasky-storage` if present
- [ ] Run `uv sync` to update dependencies

**Validation**: CLI installs with correct dependencies

---

## Phase 5: Testing and Documentation

### Task 5.1: Write integration tests for CLI with config
- [ ] Create `packages/tasky-cli/tests/test_projects_integration.py`
- [ ] Test `project init` creates config file
- [ ] Test `project init --backend json`
- [ ] Test `project init` with invalid backend shows error
- [ ] Test `project info` displays config
- [ ] Test `project info` without project shows error

**Validation**: Run `uv run pytest packages/tasky-cli/tests/ -v`

---

### Task 5.2: Write integration tests for task commands
- [ ] Create or update `packages/tasky-cli/tests/test_tasks_integration.py`
- [ ] Test task commands work after `project init`
- [ ] Test task commands without project show error
- [ ] Test task commands use correct backend from config
- [ ] Test invalid backend in config shows error

**Validation**: Run `uv run pytest packages/tasky-cli/tests/ -v`

---

### Task 5.3: Run full test suite
- [ ] Run `uv run pytest` from workspace root
- [ ] Verify all tests pass
- [ ] Fix any broken tests from refactoring
- [ ] Check test coverage with `uv run pytest --cov`

**Validation**: All tests pass, coverage ≥80%

---

### Task 5.4: Manual CLI testing
- [ ] Create new test directory
- [ ] Run `tasky project init` and verify config created
- [ ] Run `tasky project info` and verify output
- [ ] Run `tasky task create "Test" "Details"`
- [ ] Run `tasky task list` and verify task appears
- [ ] Test in directory without project (should show error)
- [ ] Test with subdirectory (should find parent project)
- [ ] Test `project init --backend json` explicitly

**Validation**: All manual tests work as expected

---

### Task 5.5: Update documentation
- [ ] Update `README.md` with configuration examples
- [ ] Document `project init --backend` option
- [ ] Document `project info` command
- [ ] Add section explaining backend selection
- [ ] Add example of `.tasky/config.json` format
- [ ] Document how to add new backends (developer guide)

**Validation**: Documentation is clear and complete

---

### Task 5.6: Update AGENTS.md if needed
- [ ] Review architecture changes
- [ ] Update package descriptions if necessary
- [ ] Ensure new patterns are documented
- [ ] Verify build/test commands are current

**Validation**: AGENTS.md reflects new structure

---

### Task 5.7: Run linting and formatting
- [ ] Run `uv run ruff check --fix`
- [ ] Run `uv run ruff format`
- [ ] Fix any linting issues
- [ ] Commit formatted code

**Validation**: Ruff passes with no errors

---

## Summary

**Total Tasks**: 37  
**Estimated Time**: 6-8 hours

**Dependencies**:
- Phase 2 requires Phase 1 complete
- Phase 3 requires Phase 2 complete  
- Phase 4 requires Phase 2 and 3 complete
- Phase 5 requires all previous phases complete

**Critical Path**:
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

**Parallelizable Work**:
- Tests can be written alongside implementation within each phase
- Documentation can be drafted during implementation

---

## Completion Checklist

Mark each phase complete when all its tasks are done:

- [ ] Phase 1: Foundation (tasky-projects)
- [ ] Phase 2: Registry and Factory (tasky-settings)
- [ ] Phase 3: Backend Self-Registration (tasky-storage)
- [ ] Phase 4: CLI Integration
- [ ] Phase 5: Testing and Documentation

**Final Validation**: Run `uv run pytest && uv run ruff check` successfully
