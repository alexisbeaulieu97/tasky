## 1. Error Protocol Decoupling

- [ ] 1.1 Define `StorageErrorProtocol` in `tasky-tasks` (domain layer)
- [ ] 1.2 Update `TaskService` to use protocol instead of direct `StorageDataError` import
- [ ] 1.3 Implement protocol in `tasky-storage.errors` module
- [ ] 1.4 Update all service methods to use protocol
- [ ] 1.5 Add tests verifying protocol works with mock implementations
- [ ] 1.6 Run full test suite: `uv run pytest --cov=packages`

## 2. Circular Import Resolution

- [ ] 2.1 Identify all local imports in modules (grep for "from.*import" inside functions)
- [ ] 2.2 For `TaskModel.transition_to()`, move `InvalidStateTransitionError` to shared exceptions module
- [ ] 2.3 Update all imports to use module-level imports (remove local imports)
- [ ] 2.4 Add type annotations to verify no circular imports remain
- [ ] 2.5 Run `uv run pyright` to verify no import issues
- [ ] 2.6 Add test to verify modules can be imported in any order

## 3. High-Complexity Function Refactoring

- [ ] 3.1 Refactor `list_command` in tasks.py: extract filter formatting logic
- [ ] 3.2 Refactor `list_command` in projects.py: extract project display logic
- [ ] 3.3 Refactor `register_project` in registry.py: extract validation logic
- [ ] 3.4 Reduce all C901 violations to <10 cyclomatic complexity
- [ ] 3.5 Remove all `# noqa: C901` comments (should not be needed)
- [ ] 3.6 Run `uv run ruff check` to verify no complexity violations remain
- [ ] 3.7 Run tests to verify no behavioral changes

## 4. Docstring Completion

- [ ] 4.1 Audit all public functions for docstrings (grep for `def [^_]`)
- [ ] 4.2 Audit all private helpers for docstrings (high-complexity ones)
- [ ] 4.3 Add docstrings to every function without one:
  - [ ] 4.3.1 `packages/tasky-projects/registry.py` private methods
  - [ ] 4.3.2 `packages/tasky-storage/backends/` helper methods
  - [ ] 4.3.3 `packages/tasky-cli/commands/` helper functions
- [ ] 4.4 Include parameter descriptions and return type explanations
- [ ] 4.5 Add examples for complex functions (especially storage operations)
- [ ] 4.6 Verify all docstrings follow PEP 257 style

## 5. Architecture Decision Records (ADRs)

- [ ] 5.1 Create `docs/architecture/adr/` directory
- [ ] 5.2 Create ADR template: `0000-template.md`
- [ ] 5.3 Document ADR-001: Backend Registry Pattern (why self-registration?)
- [ ] 5.4 Document ADR-002: Error Handling Strategy (domain vs infrastructure)
- [ ] 5.5 Document ADR-003: Configuration Hierarchy (settings precedence)
- [ ] 5.6 Document ADR-004: Project Registry Storage (why .json not database?)
- [ ] 5.7 Create index: `docs/architecture/adr/README.md` linking all ADRs
- [ ] 5.8 Link ADRs from CLAUDE.md so developers find them

## 6. Code Quality Validation

- [ ] 6.1 Run `uv run pytest --cov=packages --cov-fail-under=80`
- [ ] 6.2 Verify coverage doesn't decrease
- [ ] 6.3 Run `uv run ruff check --fix` (should have no violations)
- [ ] 6.4 Run `uv run pyright` (should have no errors)
- [ ] 6.5 Verify no `# noqa` comments remain (except justifiable ones)
- [ ] 6.6 Verify circular imports are resolved (import order independence test)

## 7. Documentation & Communication

- [ ] 7.1 Update CLAUDE.md with links to ADRs
- [ ] 7.2 Add section to IMPLEMENTATION_ROADMAP.md explaining Phase 7 purpose
- [ ] 7.3 Create ARCHITECTURE.md overview if it doesn't exist
- [ ] 7.4 Document how to add new error types without creating coupling
- [ ] 7.5 Document module import guidelines for new contributors
