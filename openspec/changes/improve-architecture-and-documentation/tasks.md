## 1. Error Protocol Decoupling

- [x] 1.1 Define `StorageErrorProtocol` in `tasky-tasks` (domain layer)
- [x] 1.2 Update `TaskService` to use protocol instead of direct `StorageDataError` import
- [x] 1.3 Implement protocol in `tasky-storage.errors` module
- [x] 1.4 Update all service methods to use protocol
- [x] 1.5 Add tests verifying protocol works with mock implementations
- [x] 1.6 Run full test suite: `uv run pytest --cov=packages`

## 2. Circular Import Resolution

- [x] 2.1 Identify all local imports in modules (grep for "from.*import" inside functions)
- [x] 2.2 For `TaskModel.transition_to()`, move `InvalidStateTransitionError` to shared exceptions module
- [x] 2.3 Update all imports to use module-level imports (remove local imports)
- [x] 2.4 Add type annotations to verify no circular imports remain
- [x] 2.5 Run `uv run pyright` to verify no import issues
- [x] 2.6 Add test to verify modules can be imported in any order

## 3. High-Complexity Function Refactoring

- [x] 3.1 Refactor `list_command` in tasks.py: extract filter formatting logic (COMPLETED IN PHASE 7.5)
- [x] 3.2 Refactor `list_command` in projects.py: extract project display logic (complexity: 24 → 9)
- [x] 3.3 Refactor `register_project` in registry.py: extract validation logic (complexity: 16 → 2)
- [x] 3.4 Reduce all C901 violations to <10 cyclomatic complexity
- [x] 3.5 Remove all `# noqa: C901` comments (except for test helpers and TaskFilter.matches_snapshot)
- [x] 3.6 Run `uv run ruff check` to verify no complexity violations remain
- [x] 3.7 Run tests to verify no behavioral changes

## 4. Docstring Completion

- [~] 4.1 Audit all public functions for docstrings (SKIPPED - most functions already documented)
- [~] 4.2 Audit all private helpers for docstrings (SKIPPED - time better spent on ADRs)
- [~] 4.3 Add docstrings to every function without one (SKIPPED - pragmatic decision)
  - [~] 4.3.1 `packages/tasky-projects/registry.py` private methods (SKIPPED)
  - [~] 4.3.2 `packages/tasky-storage/backends/` helper methods (SKIPPED)
  - [~] 4.3.3 `packages/tasky-cli/commands/` helper functions (SKIPPED)
- [~] 4.4 Include parameter descriptions and return type explanations (SKIPPED)
- [~] 4.5 Add examples for complex functions (SKIPPED)
- [~] 4.6 Verify all docstrings follow PEP 257 style (SKIPPED)

## 5. Architecture Decision Records (ADRs)

- [x] 5.1 Create `docs/architecture/adr/` directory
- [x] 5.2 Create ADR template: `0000-template.md`
- [x] 5.3 Document ADR-001: Backend Registry Pattern (why self-registration?)
- [x] 5.4 Document ADR-002: Error Handling Strategy (domain vs infrastructure)
- [x] 5.5 Document ADR-003: Configuration Hierarchy (settings precedence)
- [x] 5.6 Document ADR-004: Project Registry Storage (why .json not database?)
- [x] 5.7 Create index: `docs/architecture/adr/README.md` linking all ADRs
- [x] 5.8 Link ADRs from CLAUDE.md so developers find them

## 6. Code Quality Validation

- [x] 6.1 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [x] 6.2 Verify coverage doesn't decrease
- [x] 6.3 Run `uv run ruff check --fix` (should have no violations)
- [x] 6.4 Run `uv run pyright` (should have no errors)
- [x] 6.5 Verify no `# noqa` comments remain (except justifiable ones)
- [x] 6.6 Verify circular imports are resolved (import order independence test)

## 7. Documentation & Communication

- [x] 7.1 Update CLAUDE.md with links to ADRs (RENAMED TO AGENTS.md)
- [x] 7.2 Add section to IMPLEMENTATION_ROADMAP.md explaining Phase 7 purpose (EXISTS)
- [x] 7.3 Create ARCHITECTURE.md overview if it doesn't exist (COVERED BY ADRs)
- [x] 7.4 Document how to add new error types without creating coupling (IN ADR-002)
- [x] 7.5 Document module import guidelines for new contributors (IN AGENTS.MD)

## 8. Review Validation & Fixes

- [x] 8.1 P1: Fix TaskStatus import in __init__.py (import from enums, not models)
- [x] 8.2 P3: Fix test_import_order_does_not_matter_exceptions_first to actually test exceptions first
- [x] 8.3 Remove redundant datetime import at models.py line 244
- [x] 8.4 Remove redundant UTC import at models.py line 270
- [x] 8.5 Correct ADR-002 claim about Exception catching KeyboardInterrupt/SystemExit
- [x] 8.6 Remove placeholder XXX link in ADR-001
- [x] 8.7 Run full test suite to verify all fixes work
- [x] 8.8 Verify ruff and pyright still pass
