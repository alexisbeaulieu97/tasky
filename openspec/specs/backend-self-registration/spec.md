# backend-self-registration Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
### Requirement: JSON backend self-registration

The JSON storage backend SHALL automatically register itself with the global backend registry upon module import. **The `tasky_settings` factory SHALL ensure this import happens automatically when needed.**

#### Scenario: JSON backend registers on import

**Given** the tasky_settings.registry is available
**When** `tasky_storage` is imported (either explicitly or via factory initialization)
**Then** the "json" backend MUST be registered in the global registry
**And** registry.get("json") MUST return `JsonTaskRepository.from_path`

#### Scenario: Registration is idempotent

**Given** tasky_storage has been imported once
**When** tasky_storage is imported again (or factory initialization runs multiple times)
**Then** the "json" backend MUST remain registered
**And** no errors MUST be raised
**And** the registry state MUST be unchanged

#### Scenario: Graceful handling when registry unavailable

**Given** tasky_settings is not installed (testing isolation)
**When** I import tasky_storage
**Then** no ImportError MUST be raised
**And** the backend MUST function normally (not registered but usable)

---

### Requirement: Factory method for backend registration

The JSON repository SHALL provide a factory class method suitable for backend registration.

#### Scenario: Factory creates repository from path

```gherkin
Given a path "/home/user/project/.tasky/tasks.json"
When I call JsonTaskRepository.from_path(path)
Then it returns a JsonTaskRepository instance
And the repository uses a JsonStorage pointing to that path
And the storage file is initialized if it doesn't exist
```

#### Scenario: Factory is compatible with BackendFactory protocol

```gherkin
Given the BackendFactory type requires: Callable[[Path], TaskRepository]
And JsonTaskRepository.from_path has signature: (Path) -> JsonTaskRepository
When I register it with registry.register("json", JsonTaskRepository.from_path)
Then type checkers report no errors
And the registration succeeds at runtime
```

---

### Requirement: Backend initialization pattern documentation

The backend registration initialization pattern MUST be documented clearly for future backend implementers.

**Rationale**: Future backends (SQLite, PostgreSQL) need to follow the same self-registration pattern. Clear documentation prevents mistakes and ensures consistency.

#### Scenario: Registration pattern documented in factory

**Given** a developer reading `tasky_settings/factory.py`
**When** they examine the `_ensure_backends_registered()` function
**Then** the docstring MUST explain why backends are imported
**And** the docstring MUST describe the self-registration pattern
**And** the docstring MUST provide guidance for future backend authors

#### Scenario: Registration pattern documented in storage module

**Given** a developer reading `tasky_storage/__init__.py`
**When** they examine the registration code
**Then** comments MUST explain how backend self-registration works
**And** comments MUST reference the factory's automatic initialization
**And** the pattern MUST be clear enough to serve as a template for new backends

---

