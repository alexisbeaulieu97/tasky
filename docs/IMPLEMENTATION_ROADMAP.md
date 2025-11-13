# Tasky Implementation Roadmap
## 10-Change Strategic Plan (Nov 2025)

This roadmap organizes all 10 OpenSpec changes in optimal implementation order, accounting for dependencies, build-up of foundation features, and risk management.

---

## Overview

**Total Effort**: ~35.5-40.5 hours of implementation
**Phases**: 5 sequential phases (1, 1.5, 2, 3, 4, 4.4, 5)
**Test Gate**: After each phase, run `uv run pytest` to ensure all tests still pass

## Change Checklist

Tick off each change as you complete it (mirrors the execution order below).

- [x] 1.1 `add-task-create-command`
- [ ] 1.2 `enhance-task-list-output`
- [ ] 1.3 `add-task-show-command`
- [ ] 1.4 `add-task-update-command`
- [ ] 1.5 `ensure-storage-backend-registration`
- [ ] 2.1 `add-sqlite-backend`
- [ ] 3.1 `add-task-filtering`
- [ ] 3.2 `add-advanced-filtering`
- [ ] 3.3 `add-task-import-export`
- [ ] 4.1 `add-coverage-reporting`
- [ ] 4.2 `standardize-config-format`
- [ ] 4.3 `implement-project-list`
- [ ] 4.4 `align-tasky-projects-format`
- [ ] 5.1 `add-project-registry`

---

## Phase 1: Core CLI Completeness (8-10 hours)
**Goal**: Make tasky immediately usable from the command line for basic workflows

### 1.1 `add-task-create-command` ⭐ START HERE
**Why First**:
- Fundamental operation; blocks all downstream usage
- Users cannot do anything without ability to create tasks
- No dependencies; implements existing service layer
- ~2.5 hours

**What it enables**:
- Users can now create tasks
- After this, task list has content to work with

**Depends on**: Nothing
**Enables**: All other task commands

```bash
/openspec:apply add-task-create-command
```

---

### 1.2 `enhance-task-list-output`
**Why second**:
- Show newly created tasks effectively
- Provides context (IDs, status) needed for other commands
- Complements create command immediately
- Users see their work
- ~4 hours

**What it enables**:
- Task IDs visible in list (required for show/update/complete/cancel commands)
- Status indicators make task state obvious
- Users can see what they created with create command

**Depends on**: `add-task-create-command` (needs tasks to display)
**Enables**: `add-task-show-command`, `add-task-update-command`, filtering commands

**Interdependencies**:
- Tests should verify that tasks created by `add-task-create-command` display correctly with enhanced format
- Task IDs from create command must be copy-paste-able from list output

```bash
/openspec:apply enhance-task-list-output
```

---

### 1.3 `add-task-show-command`
**Why third**:
- Users now have IDs from list output
- Can inspect individual task details
- Complements list command for deep inspection
- ~2.5 hours

**What it enables**:
- Users can view full task metadata
- Verify task state before operations (complete/cancel/update)

**Depends on**: `enhance-task-list-output` (IDs in list output)
**Enables**: `add-task-update-command` (can verify before updating)

```bash
/openspec:apply add-task-show-command
```

---

### 1.4 `add-task-update-command`
**Why fourth**:
- Users can now fix typos after creation
- Completes basic CRUD (Create, Read, Update missing)
- Uses task IDs from list command
- ~2.75 hours

**What it enables**:
- Users can correct task metadata
- Full task editing workflow

**Depends on**: `enhance-task-list-output` (for task IDs)
**Enables**: Delete command when added (part of CRUD)

**Testing note**:
- Test updating tasks created by `add-task-create-command`
- Verify updated tasks display correctly in `enhance-task-list-output`
- Test with task IDs from list command

```bash
/openspec:apply add-task-update-command
```

---

## Phase 1 Verification Checkpoint ✓
After implementing Phase 1, users should be able to:
- Create tasks with `tasky task create NAME DETAILS`
- List tasks with status indicators and IDs: `tasky task list`
- View task details: `tasky task show TASK_ID`
- Update tasks: `tasky task update TASK_ID --name NEW_NAME`
- Existing state change commands still work: `complete`, `cancel`, `reopen`

```bash
# Run full test suite
uv run pytest
# Verify all 213+ tests pass
```

---

## Phase 1.5: Backend Registry Initialization (0.5 hours)
**Goal**: Ensure storage backends are automatically registered; fix hidden dependency

### 1.5 `ensure-storage-backend-registration` ⭐ CRITICAL FIX
**Why after Phase 1, before Phase 2**:
- Fixes hidden dependency discovered in code review
- `create_task_service()` relies on `tasky_storage` import side-effect
- Must be fixed before Phase 2 (SQLite backend) to prevent KeyError failures
- Quick fix (~0.5 hours) with high priority
- Non-breaking change

**What it enables**:
- `create_task_service()` works without explicit `tasky_storage` import
- Cleaner host implementations (CLI, API, etc.)
- Foundation for Phase 2 (SQLite backend) and beyond

**Depends on**: Phase 1 complete (nothing more)
**Enables**: Phase 2 (SQLite backend works reliably)

**What changes**:
- Update `tasky_settings/__init__.py` or `factory.py` to ensure backends are registered on first use
- Add test to verify `create_task_service()` works in isolation
- Document the backend registration pattern for future maintainers

```bash
/openspec:apply ensure-storage-backend-registration
```

---

## Phase 1.5 Verification Checkpoint ✓
After Phase 1.5, verify:
- `create_task_service()` works without explicit `tasky_storage` import
- Backend registry is initialized correctly
- No breaking changes to existing code

```bash
uv run pytest
# Verify all tests pass
```

---

## Phase 2: Storage Architecture Validation (7 hours)
**Goal**: Prove swappable backend architecture works with production-quality storage

### 2.1 `add-sqlite-backend` ⭐ ONLY ONE IN THIS PHASE
**Why standalone phase**:
- Validates the entire backend-registry and self-registration patterns
- Requires significant implementation (32 tasks, 7 hours)
- Should complete cleanly before adding more CLI features
- Demonstrates architectural strength
- Phase 1.5 ensures registry is initialized correctly

**What it enables**:
- Users can choose between JSON and SQLite backends
- Validates that adding new backends is "just an implementation" of the protocol
- Foundation for future backends (PostgreSQL, etc.)

**Depends on**: Phase 1.5 (backend registry initialization)
**Enables**: All subsequent changes work with either backend

**Implementation concern**:
- Ensure JSON and SQLite backends produce identical filtering/ordering behavior
- Test all Phase 1 CLI features work with both backends

```bash
/openspec:apply add-sqlite-backend
```

---

## Phase 2 Verification Checkpoint ✓
After Phase 2, users should be able to:
- Initialize with SQLite: `tasky project init --backend sqlite`
- Use all Phase 1 CLI features with SQLite backend
- Verify JSON and SQLite backends produce identical behavior
- Run all CLI tests against both backends

```bash
# Run full test suite with coverage
uv run pytest --cov=packages --cov-report=term-missing
# Verify ≥80% coverage
```

---

## Phase 3: Advanced Features (14-16 hours)
**Goal**: Add sophisticated capabilities that unlock new use cases

### 3.1 `add-task-filtering`
**Why first in Phase 3**:
- Foundation for all other filtering capabilities
- Adds status-only filtering (`--status pending/completed/cancelled`)
- Introduces repository-level filtering pattern
- Quick win (~2-3 hours)
- Required before advanced filtering can be implemented

**What it enables**:
- Users can filter by status: `tasky task list --status pending`
- Foundation for advanced filtering (date range + text search)
- Repository layer: `get_tasks_by_status()` method
- Service convenience methods: `get_pending_tasks()`, etc.

**Depends on**: Phase 2 complete (works with both JSON and SQLite)
**Enables**: `add-advanced-filtering` (builds on status filtering)

**Testing note**:
- Test filtering each status value
- Test service convenience methods
- Verify efficiency with 1000+ tasks
- Test with both JSON and SQLite backends

```bash
/openspec:apply add-task-filtering
```

---

### 3.2 `add-advanced-filtering`
**Why second in Phase 3**:
- Builds on status filtering from 3.1
- Adds date range and text search capabilities
- Foundation for import/export (search before exporting)
- ~4 hours
- Medium complexity (TaskFilter model, repository updates)

**What it enables**:
- Users can find tasks by date range: `--created-after 2025-11-01`
- Users can search task content: `--search "bug fix"`
- Combine filters: `--status pending --created-after 2025-11-01`

**Depends on**: `add-task-filtering` (builds on status filtering)
**Enables**: `add-task-import-export` (can filter before exporting)

**Testing note**:
- Test date filtering with tasks created at different times
- Test search across name and details
- Test combining status + date + search filters
- Test with both JSON and SQLite backends

```bash
/openspec:apply add-advanced-filtering
```

---

### 3.3 `add-task-import-export`
**Why third in Phase 3**:
- Users can now backup tasks
- Foundational for disaster recovery
- Complex implementation (52+ scenarios, 4 hours for export + import)
- Advanced filtering enhances use case (can export filtered results)
- Requires both filtering features to be in place

**What it enables**:
- Users can backup: `tasky task export backup.json`
- Users can restore: `tasky task import backup.json --strategy replace`
- Users can merge: `tasky task import tasks.json --strategy merge`
- Can filter before exporting (combines with advanced filtering)
- Templates and sharing

**Depends on**: `add-advanced-filtering` (filters can be applied before export)
**Enables**: Cross-project migrations, backup workflows

**Interdependencies**:
- Export should work with `add-advanced-filtering` results
- Import should work with both JSON and SQLite backends
- Dry-run mode should not actually modify anything

```bash
/openspec:apply add-task-import-export
```

---

## Phase 3 Verification Checkpoint ✓
After Phase 3, users should be able to:
- Filter by status: `tasky task list --status pending`
- Filter by multiple criteria: `tasky task list --status pending --search "urgent" --created-after 2025-11-01`
- Export all tasks: `tasky task export backup.json`
- Export filtered results: `tasky task export filtered.json --status completed`
- Restore tasks: `tasky task import backup.json`
- Use merge strategy to combine task lists

---

## Phase 4: Polish & Infrastructure (8-9 hours)
**Goal**: Improve code quality, user experience, and project maintainability

### 4.1 `add-coverage-reporting`
**Why first in Phase 4**:
- Tooling-only, no API changes
- Should run after all features implemented to measure real coverage
- Enable CI gates before merging Phase 3 features
- ~2 hours
- Quick win

**What it enables**:
- Coverage reports show which code is tested
- CI can enforce 80% threshold
- Developers see gaps in testing

**Depends on**: All Phase 1-3 features (measures their coverage)
**Enables**: Quality gates for future PRs

```bash
/openspec:apply add-coverage-reporting
```

---

### 4.2 `standardize-config-format`
**Why second in Phase 4**:
- Non-breaking (auto-converts legacy JSON)
- User-facing improvement (cleaner config)
- Should happen before project-list command (both work with config)
- ~6-7 hours (includes migration logic)

**What it enables**:
- Single TOML format for all config
- Users see consistent format everywhere
- Cleaner codebase (one serialization format)

**Depends on**: Nothing (standalone)
**Enables**: `implement-project-list` (works with TOML config)

**Testing note**:
- Test new projects create .tasky/config.toml
- Test legacy .tasky/config.json auto-converts
- Test settings hierarchy still works correctly

```bash
/openspec:apply standardize-config-format
```

---

### 4.3 `implement-project-list`
**Why last**:
- Low blocking risk (stub exists, no breaking changes)
- Good final polish feature
- Completes project management basics
- ~3 hours
- Users can discover their projects

**What it enables**:
- Users can find projects: `tasky project list`
- Project management basics complete
- Foundation for project administration

**Depends on**: `standardize-config-format` (reads standardized config)
**Enables**: Future project management features

**Testing note**:
- Test finding projects in current directory
- Test recursive search
- Test custom root directory
- Test with both config.toml (new) and auto-converted files

```bash
/openspec:apply implement-project-list
```

---

## Phase 4 Verification Checkpoint ✓
After Phase 4, all features are complete and polished:
- Coverage reports available: Check `htmlcov/index.html`
- All config files use TOML format
- Users can discover projects: `tasky project list`
- All tests pass with ≥80% coverage

```bash
# Final verification
uv run pytest --cov=packages --cov-fail-under=80
uv run ruff check --fix
uv run ruff format
```

---

## Implementation Commands Quick Reference

```bash
# Phase 1 - Core CLI (run in order)
/openspec:apply add-task-create-command
/openspec:apply enhance-task-list-output
/openspec:apply add-task-show-command
/openspec:apply add-task-update-command

# Phase 1.5 - Critical Fix (BEFORE Phase 2)
/openspec:apply ensure-storage-backend-registration

# Phase 2 - Backend Validation
/openspec:apply add-sqlite-backend

# Phase 3 - Advanced Features (run in order)
/openspec:apply add-task-filtering
/openspec:apply add-advanced-filtering
/openspec:apply add-task-import-export

# Phase 4 - Polish (run in order)
/openspec:apply add-coverage-reporting
/openspec:apply standardize-config-format
/openspec:apply implement-project-list
/openspec:apply align-tasky-projects-format

# Phase 5 - Global Project Registry
/openspec:apply add-project-registry
```

---

## Dependency Graph

```
# Phase 1: Core CLI
add-task-create-command (START)
    ↓
enhance-task-list-output
    ├→ add-task-show-command
    │       ↓
    │   add-task-update-command
    └→ (both complete Phase 1)
        ↓
    ensure-storage-backend-registration (Phase 1.5 - CRITICAL FIX)
        ↓
    add-sqlite-backend (Phase 2)
        ↓
    add-task-filtering (Phase 3.1 - status filtering)
        ↓
    add-advanced-filtering (Phase 3.2 - date + search)
        ↓
    add-task-import-export (Phase 3.3)

# Phase 4: Polish (can run after all features)
add-coverage-reporting (after Phase 3)
standardize-config-format (any time after Phase 3)
    ↓
implement-project-list (Phase 4.3)
    ↓
align-tasky-projects-format (Phase 4.4 - quick 0.5h fix)
    ↓
add-project-registry (Phase 5 - 5-6 hours)
```

---

## Risk Mitigation Strategy

### Per-Phase Testing
After each phase, before starting the next:
```bash
uv run pytest
# Verify all tests pass (not just new ones)
```

### Cross-Backend Validation
After Phase 2, every CLI test should run against both JSON and SQLite:
- If test uses storage, parameterize it
- Both backends should produce identical results

### Breaking Changes
Only Phase 4's `standardize-config-format` is breaking:
- Mitigated with auto-conversion
- Happens late in cycle after features stable
- Users with legacy config.json see one-time warning

### Rollback Points
- After Phase 1: Full CRUD, basic CLI complete
- After Phase 2: Architecture validated
- After Phase 3: All features except polish

---

## Effort Breakdown

| Phase | Changes | Tasks | Hours | Complexity |
|-------|---------|-------|-------|------------|
| 1 | 4 | 50+ | 8-10 | Medium |
| 1.5 | 1 | 12 | 0.5 | Low |
| 2 | 1 | 32 | 7 | High |
| 3 | 3 | 59+ | 14-16 | High |
| 4 | 3 | 28 | 8-9 | Low-Med |
| 4.4 | 1 | 13 | 0.5 | Low |
| 5 | 1 | 48 | 18-20 | High |
| **TOTAL** | **14** | **242+** | **56-62** | **Balanced** |

---

## Success Criteria

### Phase 1 ✓
- [ ] Users can create, list, show, and update tasks
- [ ] All 213+ tests pass
- [ ] CLI workflow is intuitive

### Phase 2 ✓
- [ ] SQLite backend is production-ready
- [ ] All CLI features work with both JSON and SQLite
- [ ] Architecture validation complete

### Phase 3 ✓
- [ ] Advanced filtering works correctly
- [ ] Import/export covers all scenarios
- [ ] Data portability achieved

### Phase 4 ✓
- [ ] Coverage ≥80%
- [ ] Configuration standardized on TOML
- [ ] Project discoverability complete

---

---

## Phase 4.4: Architectural Alignment (0.5 hours)
**Goal**: Fix format mismatch identified in code review; prepare for Phase 5

### 4.4 `align-tasky-projects-format`
**Why after Phase 4.3**:
- Quick fix with no new features
- Prepares foundation for Phase 5 registry feature
- Addresses architectural debt (JSON vs TOML mismatch)
- ~0.5 hours

**What it enables**:
- `tasky-projects` package uses TOML format consistently
- ProjectConfig can read/write `.tasky/config.toml` (currently only reads/writes JSON)
- Foundation for Phase 5 registry feature

**Depends on**: `standardize-config-format` (Phase 4.2)
**Enables**: Phase 5 registry implementation

```bash
/openspec:apply align-tasky-projects-format
```

---

## Phase 5: Global Project Registry (5-6 hours)
**Goal**: Enable `tasky` commands to work from anywhere by discovering and managing projects globally

### 5.1 `add-project-registry`
**Why separate phase**:
- Builds on Phases 1-4 foundation
- Non-blocking feature (existing workflow still works)
- Enables cross-project workflows
- ~5-6 hours with 3 sub-components

**What it enables**:
- Users can track multiple projects in `~/.tasky/registry.json`
- `tasky project list` shows all registered projects
- Future: `tasky task <cmd> --project <name>` works from anywhere
- Foundation for project metadata (created_at, last_accessed, etc.)

**Depends on**: Phase 4 complete (especially Phase 4.4 alignment)
**Enables**: Cross-project commands and advanced project workflows

```bash
/openspec:apply add-project-registry
```

---

## Success Criteria

### Phase 1 ✓
- [ ] Users can create, list, show, and update tasks
- [ ] All tests pass
- [ ] CLI workflow is intuitive

### Phase 1.5 ✓
- [ ] Backend registry is automatically initialized
- [ ] `create_task_service()` works without explicit `tasky_storage` import
- [ ] No breaking changes to existing code

### Phase 2 ✓
- [ ] SQLite backend is production-ready
- [ ] All CLI features work with both JSON and SQLite
- [ ] Architecture validation complete

### Phase 3 ✓
- [ ] Status filtering works correctly
- [ ] Advanced filtering (date + search) works with combined criteria
- [ ] Import/export covers all scenarios and merge strategies
- [ ] Data portability achieved

### Phase 4 ✓
- [ ] Coverage ≥80%
- [ ] Configuration standardized on TOML
- [ ] Project discoverability complete
- [ ] tasky-projects format aligned with TOML

### Phase 5 ✓
- [ ] Global project registry implemented
- [ ] `tasky project list` lists all registered projects
- [ ] Projects can be discovered from anywhere

---

## After Implementation: Archival Process

Once each change is merged (after PR):
```bash
openspec archive add-task-create-command --yes
openspec archive enhance-task-list-output --yes
# ... continue for all changes

# Final validation
openspec validate --specs
```

This moves completed changes to `openspec/changes/archive/YYYY-MM-DD-<name>/` and updates the specs to reflect the new state.

---

## Architectural Vision

**tasky** is designed with clear separation of concerns:

- **tasky-tasks**: Task domain (models, services, business rules)
- **tasky-projects**: Project domain (registry, discovery, metadata)
- **tasky-storage**: Storage adapters (JSON, SQLite, etc.)
- **tasky-settings**: Configuration wiring and dependency injection
- **tasky-cli**: User-facing commands and presentation

**Phase 5** completes the architecture by:
1. Implementing the project registry in `tasky-projects`
2. Enabling project discovery across the filesystem
3. Supporting workflows that span multiple projects

---

## Questions Before Starting?

- Want to adjust the order?
- Want to split any phase?
- Want to implement any changes in parallel?
- Need clarification on any dependencies?

Start with Phase 1.1 when ready! 🚀
