# Settings Architecture

## Separation of Concerns
- **Global settings** (`tasky_root/config.json`) store only user-configured values that impact global behavior.
- **Project settings** live inside each repo under `.tasky/`, keeping project metadata/versionable alongside the code.
- Settings objects (Pydantic models) remain declarative; they hold values and validation but don’t embed orchestration logic.

## Passive Config Objects
- `TaskySettings` exposes resolved configuration (env overrides + JSON) for other layers.
- No business logic resides inside the settings module—consumers in `tasky-core` or adapters decide how to act on values.

## ProjectSettingsService
- Encapsulates registry paths, project discovery, and repository factories.
- Methods like `initialise_project`, `ensure_project_initialised`, `build_task_service`, and `list_registered_projects` ensure all filesystem touches flow through an injectable service.
- CLI/adapters call module-level helpers (`tasky_settings.projects.*`), which simply delegate to a scoped `ProjectSettingsService`.
- When a project's `tasks_file` ends with `.sqlite`/`.db`, the service now switches to the normalized `SQLiteTaskRepository`; otherwise it defaults to the JSON-backed repository. Projects can therefore opt into a relational backend simply by editing `.tasky/config.json`.
- Repository creation is delegated to `TaskRepositoryFactory`, which callers can replace/inject when custom storage backends or caching layers are required. The default factory resolves the configured path, selects either the JSON or SQLite repository, and returns the correct adapter.
- Global registry adapters are selected via `ProjectRegistryRepositoryFactory`, which builds JSON or SQLite repositories based on the configured backend before passing them to the core registry ports.
- Global registry storage is configurable via the `TaskySettings.registry_backend` field. JSON remains the default, while the optional SQLite backend (`projects.db`) enables concurrent-safe writes. When switching to SQLite, the service migrates any existing `projects.json` file automatically before handling new commands.
- `update_project_config` powers the `tasky project config` CLI command: it validates supported keys (currently `tasks_file`), migrates the task dataset when the storage path changes, and touches the registry entry so `updated_at` stays current. Forced updates can overwrite existing targets; otherwise the service refuses to clobber data.
- A progress-aware `TaskService` wrapper refreshes cached task counts after every mutation (add/remove/import/complete/reopen/update). Counts are stored on the registry entry (`total_tasks`, `completed_tasks`, `progress_updated_at`) via `update_project_progress`, so read-heavy commands (`tasky project list`) can return immediately without scanning every tasks repository. `ProjectSettingsService.refresh_project_progress` exposes the same logic for forced refreshes (e.g., `--refresh-progress`).

## ConfigRepository
- Wraps low-level JSON persistence (`read`/`write`) for the global Tasky config.
- Handles atomic writes via temp files and invalidates settings caches after successful commits.
- Tests can instantiate the repository with a temp directory to verify behaviour without monkeypatching globals.

## Shared Persistence Helpers
- Shared IO utilities live in `tasky_shared.jsonio` (for generic JSON) and `tasky_core.projects.persistence` (for project-specific config/registry helpers). They provide atomic read/write semantics, fsync guarantees, and consistent exception handling so every layer benefits from the same durability traits without re-implementing file logic.
- Project-oriented helpers operate on `<project>/.tasky/config.json`, while global helpers target the Tasky root (`~/.tasky/config.json`). Every caller goes through these helpers to avoid partial writes or inconsistent validation.
