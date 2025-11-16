# Tasky Implementation Roadmap
## 18-Change Strategic Plan (Nov 2025)

This roadmap organizes all 18 OpenSpec changes across Phases 1-8 in optimal implementation order, accounting for dependencies, build-up of foundation features, and risk management.

---

## Overview

**Total Effort (Phases 1-6)**: ~56-62 hours (COMPLETE ✅)
**Total Effort (Phases 7-7b)**: ~174 hours of code quality + CLI improvements
**Total Effort (Phases 8+)**: TBD (MCP servers, hooks, advanced features)
**Phases**: 6 completed (1, 1.5, 2, 3, 4, 4.4, 5, 6) + 2 in progress (7-7b) + future phases
**Test Gate**: After each phase, run `uv run pytest` to ensure all tests still pass

## Change Checklist

Tick off each change as you complete it (mirrors the execution order below).

### ✅ Phases 1-6: COMPLETE (Foundation & Features)
- [x] 1.1 `add-task-create-command`
- [x] 1.2 `enhance-task-list-output`
- [x] 1.3 `add-task-show-command`
- [x] 1.4 `add-task-update-command`
- [x] 1.5 `ensure-storage-backend-registration`
- [x] 2.1 `add-sqlite-backend`
- [x] 3.1 `add-task-filtering`
- [x] 3.2 `add-advanced-filtering`
- [x] 3.3 `add-task-import-export`
- [x] 4.1 `add-coverage-reporting`
- [x] 4.2 `standardize-config-format`
- [x] 4.3 `implement-project-list`
- [x] 4.4 `align-tasky-projects-format`
- [x] 5.1 `add-project-registry`
- [x] 6.1 `remove-json-config-support`

### 🚀 Phase 7: Code Quality & Testing (224 tasks, ~91 hours)
- [x] 7.1 `improve-storage-backend-testing` (35 tasks, ~26h)
- [x] 7.2 `improve-cli-test-coverage` (47 tasks, ~22h)
- [ ] 7.3 `refactor-storage-duplication` (30 tasks, ~7h)
- [ ] 7.4 `improve-performance-and-safety` (42 tasks, ~21h)
- [ ] 7.5 `improve-architecture-and-documentation` (44 tasks, ~15h)

### 🎯 Phase 7b: CLI Improvements (51 tasks, ~51 hours)
- [ ] 7b.1 `add-cli-input-validators` (25 tasks, ~3h)
- [ ] 7b.2 `refactor-cli-error-handling` (26 tasks, ~2h)

### 🚀 Phase 8: AI Integration (45 tasks, ~40-50 hours)
- [ ] 8.1 `add-mcp-server` (MCP protocol integration for Claude)

### 🎯 Phase 9: Event-Driven Automation (35 tasks, ~30-40 hours)
- [ ] 9.1 `implement-task-hooks` (Lifecycle events and automation)

### 💾 Phase 10: Enterprise Features (55 tasks, ~50-60 hours)
- [ ] 10.1 `add-advanced-backends` (PostgreSQL, multi-user, audit trails)

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

### 3.1 `add-task-filtering` ✓ COMPLETED
**Status**: Previously implemented and archived (`openspec/changes/archive/2025-11-13-add-task-filtering/`)

**What it implements**:
- Status-only filtering (`--status pending/completed/cancelled`)
- Repository layer: `get_tasks_by_status()` method
- Service convenience methods: `get_pending_tasks()`, `get_completed_tasks()`, `get_cancelled_tasks()`
- CLI: `tasky task list --status <status>` command
- Full support for both JSON and SQLite backends

**Current state**:
- ✓ 14 CLI filtering tests passing
- ✓ Backend integration tests (JSON + SQLite)
- ✓ 4 specifications created and active
- ✓ All 312 tests passing

This phase established the foundation for advanced filtering capabilities. The implementation is production-ready and serves as the base for Phase 3.2.

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

# Phase 6 - Future Cleanup (Optional, flexible timeline)
/openspec:apply remove-json-config-support
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
| 6 (Optional) | 1 | 8 | 6-8 | Low-Med |
| **TOTAL (Phases 1-5)** | **11** | **242+** | **56-62** | **Balanced** |
| **TOTAL (with optional Phase 6)** | **12** | **250+** | **62-70** | **Balanced** |

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

## Phase 6: Future Cleanup & Optimization (Optional)

**Goal**: Simplify codebase after all features are stable

### 6.1 `remove-json-config-support` (Optional - Flexible Timeline)

**Why optional**:
- Cleanup task, not a feature
- Can be executed anytime after decision to remove JSON
- No blocking dependencies
- Simplifies configuration code but not required for users
- ~6-8 hours (includes comprehensive code audit)

**What it enables**:
- 100% clean codebase (zero JSON references)
- Simplified configuration logic (single TOML path)
- Reduced test maintenance (~12-15 fewer tests)
- Cleaner future configuration changes

**When to do it**:
- **Option A (Soon)**: Execute when codebase is stable if JSON removal is priority
- **Option B (Planned)**: Bundle with next major release (v2.0)
- **Option C (Defer)**: Keep JSON support if broader backwards compatibility is valued

**What changes**:
- Remove `_load_json()` method from `tasky-projects/config.py`
- Remove JSON detection from `ProjectConfig.from_file()`
- Remove JSON source handling from `tasky-settings/sources.py`
- Delete all JSON-specific test cases (~12-15 tests)
- Remove all JSON references, comments, and examples
- Update CHANGELOG with breaking change note

**Success criteria**:
- ✅ Zero JSON references in production code (`rg -i \"json\" packages/` returns nothing)
- ✅ All tests pass with ≥80% coverage
- ✅ Code reads as if TOML was always the only format
- ✅ Error messages are generic (no JSON mentions)
- ✅ CHANGELOG documents breaking change (only place mentioning removal)

**Depends on**: All Phases 1-5 (no blocking dependencies, cleanup only)
**Enables**: Cleaner future development, reduced cognitive load

```bash
/openspec:apply remove-json-config-support
```

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

---

## Phase 7: Code Quality & Testing (224 tasks, ~91 hours)
**Goal**: Bring codebase to production-ready quality with comprehensive test coverage and clean architecture

### Context
After completing all core features (Phases 1-6), comprehensive audit identified 15 substantial code quality issues:
- **Critical**: SQLite 54% coverage, CLI 69% coverage, N+1 filtering, non-atomic writes
- **High**: 100+ lines duplicate code, circular imports, high complexity, missing docs
- Issues organized into 5 strategic proposals addressing testing, performance, refactoring, and architecture

### 7.1 `improve-storage-backend-testing` ⭐ CRITICAL
**Why First**: Foundation for all storage operations. SQLite coverage (54%) blocks confidence in data safety.
**What**: Error path testing, concurrency/stress testing, backend migration tests, corruption recovery
**Tasks**: 35 | Hours: ~26 | Coverage: 54% → 80%+
**Depends on**: Nothing (standalone)
**Enables**: Phases 7.3, 7.4 can run in parallel after this provides confidence

```bash
/openspec:apply improve-storage-backend-testing
```

### 7.2 `improve-cli-test-coverage` ⭐ HIGH PRIORITY
**Why Second in Phase 7**: User-facing error handling and edge cases untested (CLI 69% coverage)
**What**: Error handler tests, command edge cases, import/export edge cases, input validation integration
**Tasks**: 47 | Hours: ~22 | Coverage: 69% → 80%+
**Depends on**: Nothing (can run in parallel with 7.1)
**Enables**: 7b.1 and 7b.2 (CLI improvements need good test foundation)

```bash
/openspec:apply improve-cli-test-coverage
```

### 7.3 `refactor-storage-duplication`
**Why Third in Phase 7**: After testing confidence is high, refactor duplicate code safely
**What**: Extract shared snapshot conversion utility, standardize serialization, remove duplicate error handling
**Tasks**: 30 | Hours: ~7 | Impact: Removes 100+ lines of duplicate code
**Depends on**: 7.1 complete (tests validate refactoring doesn't break behavior)
**Enables**: 7.4 (cleaner code for performance optimization)

```bash
/openspec:apply refactor-storage-duplication
```

### 7.4 `improve-performance-and-safety`
**Why Fourth in Phase 7**: After duplicate code removed, optimize performance patterns
**What**: Filter-first strategy (10x faster filtering), atomic writes (data safety), registry pagination
**Tasks**: 42 | Hours: ~21 | Impact: Critical performance + reliability improvements
**Depends on**: 7.3 complete (cleaner code structure for optimization)
**Enables**: Confident in handling 100k+ projects, large task datasets

```bash
/openspec:apply improve-performance-and-safety
```

### 7.5 `improve-architecture-and-documentation`
**Why Last in Phase 7**: After code is clean and tested, polish architecture
**What**: Error protocol decoupling, circular import resolution, complexity reduction, ADR creation
**Tasks**: 44 | Hours: ~15 | Impact: Cleaner architecture, better onboarding
**Depends on**: 7.1-7.4 complete (improves overall codebase quality)
**Enables**: Phase 7b (clean foundation for CLI improvements)

```bash
/openspec:apply improve-architecture-and-documentation
```

### Phase 7 Validation Checkpoint ✓
After Phase 7 completion:
- Test coverage: 82.79% → 85%+ ✅
- SQLite coverage: 54% → 80%+ ✅
- CLI coverage: 69% → 80%+ ✅
- No cyclomatic complexity violations (0 C901 noqa comments) ✅
- No circular imports ✅
- No duplicate snapshot code ✅
- All docstrings present, 4+ ADRs documented ✅

```bash
# Validation commands
uv run pytest --cov=packages --cov-fail-under=80
uv run ruff check --fix
uv run pyright
openspec validate --specs
```

---

## Phase 7b: CLI Improvements (51 tasks, ~51 hours)
**Goal**: Improve CLI user experience with input validation and error handling consolidation

### Context
Two high-value CLI improvements that should run AFTER Phase 7 testing foundation is solid.
These enhance usability and error messages, leveraging comprehensive test coverage from Phase 7.2.

### 7b.1 `add-cli-input-validators` ⭐ HIGH VALUE
**Why First in Phase 7b**: Input validation framework used by all CLI commands
**What**: Extract validation into reusable validators (UUID, date, status, priority); fail-fast before service invocation
**Tasks**: 25 | Hours: ~3 | Impact: User-friendly error messages, consistent validation
**Depends on**: 7.2 (improved CLI test coverage)
**Enables**: 7b.2 (error handling improvements integrate with validators)

```bash
/openspec:apply add-cli-input-validators
```

### 7b.2 `refactor-cli-error-handling`
**Why Second in Phase 7b**: Uses validators from 7b.1, integrated with test coverage from 7.2
**What**: Consolidate duplicate error handlers into registry-based dispatcher
**Tasks**: 26 | Hours: ~2 | Impact: Maintainable error handling, consistent exit codes
**Depends on**: 7b.1 complete (validators ready for integration)
**Enables**: Future CLI commands inherit clean error handling

```bash
/openspec:apply refactor-cli-error-handling
```

### Phase 7b Validation Checkpoint ✓
After Phase 7b completion:
- CLI validation working end-to-end ✅
- All error paths handled consistently ✅
- User-friendly messages in all scenarios ✅
- Tests pass with integrated validators ✅
- Exit codes correct (1 for user errors, 2 for internal) ✅

```bash
# Validation commands
uv run pytest --cov=packages/tasky-cli --cov-fail-under=80
uv run ruff check --fix
uv run pyright
# Manual test: try error scenarios
uv run tasky task show invalid-id  # Should show friendly error
uv run tasky task create           # Should validate input
```

---

## Phase 7-7b Execution Timeline (Recommended)

```
Week 1: Storage Foundation
  Mon-Tue: improve-storage-backend-testing (start)
  Wed-Thu: improve-cli-test-coverage (parallel)
  Fri:     Validation gate (80% coverage, all tests pass)

Week 2: Optimization & Cleanup
  Mon-Tue: refactor-storage-duplication (parallel with next)
  Wed-Thu: improve-performance-and-safety
  Fri:     Validation gate (benchmarks pass, no performance regression)

Week 3: Architecture Polish
  Mon-Wed: improve-architecture-and-documentation
  Thu:     Validation gate (no C901 violations, ADRs written)
  Fri:     Final PR review → merge Phase 7

Week 4: CLI Improvements (Optional but recommended)
  Mon-Tue: add-cli-input-validators
  Wed:     add-cli-error-handling (refactor)
  Thu:     Validation gate (CLI tests pass, error handling integrated)
  Fri:     PR review → merge Phase 7b
```

---

## Phase 8: MCP Server Integration (45 tasks, ~40-50 hours)
**Goal**: Enable Claude and other AI assistants to manage tasks via MCP protocol

### Status: ✅ PROPOSED & VALIDATED

**Why After Phase 7b**: Production-ready codebase with clean CLI error handling. MCP inherits all these improvements.

**What it does**:
- Exposes 10+ task and project operations via MCP tools
- Enables Claude to create, list, update, complete, delete tasks
- Service caching for long-lived MCP connections
- Request-scoped logging with correlation IDs
- Thread-safe concurrent request handling

**Tasks**: 45 total
- Server core (caching, logging, config): 7 tasks
- Task operations (10 tools): 12 tasks
- Project operations (4 tools): 6 tasks
- Error handling & resilience: 5 tasks
- Threading & concurrency: 6 tasks
- Integration testing: 7 tasks
- Documentation & examples: 2 tasks

**Depends on**: Phase 7b complete (clean CLI foundation)
**Enables**: AI-assisted task management, future integrations

```bash
/openspec:apply add-mcp-server
```

---

## Phase 9: Task Lifecycle Hooks (35 tasks, ~30-40 hours)
**Goal**: Enable event-driven automation and external system integration

### Status: ✅ PROPOSED & VALIDATED

**Why After Phase 8**: After MCP proves external system integration works well. Hooks follow same patterns.

**What it does**:
- 7 lifecycle events (created, updated, completed, cancelled, reopened, deleted, imported)
- Hook dispatcher and event broadcasting
- Default handlers (logging, optional CLI output)
- User-defined hooks support (`~/.tasky/hooks.py`)
- Integration with all task service methods

**Tasks**: 35 total
- Event types definition: 8 tasks
- Dispatcher implementation: 6 tasks
- Default handlers: 3 tasks
- Task service integration: 7 tasks
- CLI integration: 4 tasks
- Extension points & user hooks: 3 tasks
- Documentation & examples: 4 tasks

**Depends on**: Phase 8 complete (patterns established)
**Enables**: Workflow automation, Slack notifications, calendar sync, audit logs

```bash
/openspec:apply implement-task-hooks
```

---

## Phase 10: Advanced Storage Backends - PostgreSQL (55 tasks, ~50-60 hours)
**Goal**: Enable multi-user, enterprise-grade task management

### Status: ✅ PROPOSED & VALIDATED

**Why After Phase 9**: After hooks enable audit trail concept. PostgreSQL audit feature benefits from hook patterns.

**What it does**:
- Full PostgreSQL backend implementation (matches JSON/SQLite protocol)
- Multi-user support (project ownership, access control foundation)
- Audit trail (immutable change log)
- Transaction support with conflict detection
- Connection pooling for scalability
- Automatic schema management (migrations)

**Tasks**: 55 total
- Schema design & migrations: 9 tasks
- Backend implementation (CRUD): 10 tasks
- Transaction & concurrency: 6 tasks
- Configuration & connection pooling: 7 tasks
- Error handling & resilience: 6 tasks
- Audit trail: 6 tasks
- Testing (unit + integration): 7 tasks
- Documentation & migration guide: 7 tasks
- Multi-user foundation: 4 tasks

**Depends on**: Phase 9 complete (hooks established)
**Enables**: Shared task databases, multi-user collaboration, audit compliance

```bash
/openspec:apply add-advanced-backends
```

---

### Future Directions Beyond Phase 10

After Phase 8-10 complete, consider:
- **Cloud Storage Backends** (S3, Google Cloud for sync across devices)
- **User Management** (proper multi-user authentication, permissions)
- **API Server** (HTTP API for mobile/web clients)
- **Mobile Apps** (iOS/Android clients)
- **Analytics & Insights** (task metrics, completion trends)

---

## Next Steps

1. **Complete Phase 7** (Code Quality & Testing)
   - 5 validated proposals ready for implementation
   - ~91 hours of work, 3-week timeline
   - Brings codebase to production-ready quality

2. **Complete Phase 7b** (CLI Improvements - Optional but recommended)
   - 2 validated proposals ready for implementation
   - ~51 hours of work, 1-week timeline
   - Enhances user experience

3. **Plan Future Phases** (Phase 8+)
   - After Phase 7-7b complete, create proposals for MCP, hooks, and backends
   - Each needs comprehensive audit and specification
   - Will follow same OpenSpec-driven approach

---

## Ready to Start?

- Review Phase 7-7b proposals: `openspec list` and `openspec show <name>`
- Adjust execution order if needed
- Approve proposals when ready to begin

Questions? Check the detailed phase sections above or discuss specific proposals.

Good luck! 🚀
