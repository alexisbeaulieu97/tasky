# Tasky Project Storage Vision

## Guiding Principles
- Keep user-specific configuration inside the Tasky root directory.
- Co-locate project-specific metadata with the repository it augments.
- Support portable, version-controlled workflows without blocking local overrides.

## Tasky Root Directory
- Resolved via `TASKY_ROOT_DIR` env variable, falling back to `~/.tasky`.
- Stores global settings/configuration (`config.json`) and runtime state that should not be committed to repos.
- Remains the discovery point for all registered projects.

## Project Registration
- Introduce a `projects.json` registry under the Tasky root that tracks initialized projects.
- Each entry stores an absolute path to the project's `.tasky/` directory plus lightweight metadata (UUID, timestamps).
- On CLI startup, validate entries; gracefully drop or flag paths that no longer exist.
- Persist updates atomically to avoid corruption when multiple commands run concurrently.
- The registry backend is selectable via `TaskySettings.registry_backend` (`json` by default, `sqlite` for large/concurrent workspaces); switching to SQLite automatically migrates the on-disk JSON file into `projects.db`.

## Repository-Scoped Metadata
- When running `tasky init` inside a repository, create a `.tasky/` directory at the repo root.
- Place project-level config and state inside the `.tasky/` directory so the project remains self-contained and versionable.
- Store task data in `.tasky/tasks.json` by default; project config can override this path if needed.
- Keep this folder Tasky-managed—treat it similarly to `.git/`; avoid manual edits outside of documented hooks.
- Shareable automation (templates, workflows) can be committed, while sensitive user secrets stay outside the repo in the Tasky root.

## Project Hooks
- Projects can opt into per-command automations by creating `.tasky/hooks/` with an executable script set and a manifest named `hook.json`.
- Run `tasky project hooks scaffold` to bootstrap the directory, manifest, and sample scripts (use `--minimal` for a blank manifest or `--force` to overwrite existing files). The scaffolded samples live under `tasky_cli/templates/hooks/`, so you can customise them or add new templates centrally.
- Manifest schema:
  ```json
  {
    "version": 1,
    "hooks": [
      {
        "id": "normalize-add",
        "event": "task.pre_add",
        "command": ["python", "scripts/normalize.py"],
        "timeout": 5,
        "continue_on_error": false
      }
    ]
  }
  ```
  - `command` is an argv array executed with `cwd=.tasky/hooks/` so relative paths resolve beside the manifest.
  - Optional fields: `timeout` (seconds) and `continue_on_error` (default `false`, set `true` for best-effort hooks).
- The CLI feeds each hook a JSON payload via STDIN and exports helper env vars: `TASKY_HOOK_EVENT`, `TASKY_HOOK_ID`, `TASKY_PROJECT_ROOT`, and `TASKY_HOOKS_DIR`. Hooks may emit logs to STDERR freely; stdout is reserved for structured JSON responses.
- If a hook prints a JSON document to STDOUT, it is treated as the next payload for subsequent hooks of the same event—allowing scripts to mutate task inputs (e.g., trim names, enrich metadata, filter imports). Hooks that do not need to mutate data should simply avoid writing to STDOUT.
- Supported events (all payloads include `"event"` and `"project_path"`):
  - `task.pre_add`: `{ "name": str, "details": str, "parent_id": str | null }`
  - `task.post_add`: `{ "task": <Task JSON> }`
  - `task.pre_remove`: `{ "task_id": str }`
  - `task.post_remove`: `{ "task": <Task JSON> }`
  - `task.pre_import`: `{ "strategy": str, "tasks": [<Task JSON> ...] }`
  - `task.post_import`: `{ "strategy": str, "imported": int }`
  - `task.pre_complete`: `{ "task_id": str }`
  - `task.post_complete`: `{ "task": <Task JSON> }`
  - `task.pre_reopen`: `{ "task_id": str }`
  - `task.post_reopen`: `{ "task": <Task JSON> }`
  - `task.pre_update`: `{ "task_id": str, "name": str | null, "details": str | null }`
  - `task.post_update`: `{ "task": <Task JSON> }`
  - `project.post_init`: `{ "project_path": str, "reinitialised": bool }`
  - `project.post_forget`: `{ "project_path": str, "purged": bool }`
- Hook failures raise `HookExecutionError` unless `continue_on_error` is set, ensuring the CLI remains predictable. Post hooks are ideal for notifications/logging (set `continue_on_error=true`); pre hooks can mutate payloads (return JSON) or abort commands with descriptive errors.
- Hook manifests are cached in-process so repeated commands don’t re-parse large hook sets. Touching `hook.json` or any file under `.tasky/hooks/` automatically invalidates the cache, so edits are picked up on the next command run.

## Project Config Management
- Use `tasky project config` to inspect the current `.tasky/config.json` payload (defaults to pretty-printed JSON) or to update mutable fields like `tasks_file`. The command always goes through `ProjectSettingsService`, so validation and migrations stay centralized.
- Set new values via `--set key=value` (e.g., `--set tasks_file=tasks.sqlite`). When the tasks file changes, the service migrates the existing dataset to the new backend (JSON or SQLite) and touches the registry entry so observability stays accurate.
- When switching storage backends, the CLI prompts for confirmation unless `--force` is supplied. Passing `--force` also allows overwriting an existing target file.
- The service rejects unsupported keys and raises descriptive errors if the migration cannot proceed (e.g., target directory exists, source data is unreadable).

## Project Progress Cache
- Each registry entry now stores cached task counts (`total_tasks`, `completed_tasks`, `progress_updated_at`). Task mutations (add/remove/import/complete/reopen/update) run through a progress-aware `TaskService`, which recomputes counts once per mutation and persists them to the registry.
- `tasky project list` consumes the cached values to avoid scanning every tasks file. Use `tasky project list --refresh-progress` to force a one-off recomputation (useful after manual edits or bulk migrations).
- The cache lives beside the registry (JSON or SQLite), so it stays consistent regardless of backend and benefits remote commands that never touch the actual project storage.

## Workflow Implications
- Project discovery uses the registry to list or reopen projects, regardless of their filesystem location.
- CLI support mirrors this flow: `tasky project init` creates `.tasky/` folders and registers the project, while `tasky project list`/`tasky project unregister`/`tasky project prune` operate on the registry, and `tasky task <command>` handles task lifecycle actions inside the current project.
- Users may override the Tasky root to isolate contexts (e.g., CI environments) without touching project repos.
- Repositories can travel with their Tasky metadata, allowing seamless collaboration across machines.

## Core Layer Hooks
- Task orchestration is performed through `TaskUseCases`, which consumes `TaskRepository` implementations and manipulates hierarchies via `TaskTree`.
- Storage adapters in `tasky-storage` implement the repository protocol (e.g., `JsonTaskRepository`) and can be swapped without touching CLI logic. The hook runner (`tasky_storage.hooks.ProjectHookRunner`) also lives here so subprocess orchestration stays outside the core.
- When introducing new workflows (imports, automation), compose them through use-cases instead of embedding business logic inside CLI commands or adapters.
- Shared persistence helpers (`tasky_core/projects/persistence.py`) handle JSON loading + atomic writes (fsync + temp files) for project configs and registries so all commands benefit from the same durability guarantees.
- `TaskRepositoryFactory` (in `tasky-settings`) resolves project config paths and selects the appropriate document store (JSON vs. SQLite). `ProjectRegistryRepositoryFactory` performs the same role for the global registry, so `ProjectSettingsService` simply consumes the domain ports. Inject custom factories when a project needs alternate backends or caching policies without modifying the service.

## Lifecycle Commands
- `tasky project init/register/prune/unregister` manage registry entries and `.tasky/` metadata consistently. Additional commands such as `tasky project config` (for metadata edits) and `tasky project hooks scaffold` (automation bootstrapping) keep on-disk state aligned with the registry without manual file edits.
- When adding new lifecycle flows, document them here so contributors understand how each command interacts with the registry, config, hooks, and task datasets.
