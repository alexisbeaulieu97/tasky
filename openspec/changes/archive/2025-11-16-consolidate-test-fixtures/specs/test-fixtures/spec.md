# Spec Delta: test-fixtures

## ADDED Requirements

### Requirement: Shared Test Fixtures Module

The tasky-cli test suite SHALL provide a centralized `conftest.py` module containing shared fixtures to eliminate code duplication and ensure consistent test setup across all test files.

#### Fixture Organization

The `conftest.py` module SHALL provide:

- `runner() -> CliRunner`: Shared CLI test runner (already exists)
- `initialized_project(tmp_path, monkeypatch) -> Path`: Initialized project environment

**Constraints:**
- All fixtures SHALL use pytest's fixture discovery mechanism (no explicit imports required)
- Fixtures SHALL be session-scoped or function-scoped as appropriate
- Fixtures SHALL have comprehensive docstrings explaining their purpose and behavior
- Fixtures SHALL clean up resources automatically (leverage pytest's teardown)

#### initialized_project Fixture Contract

The `initialized_project` fixture SHALL:

1. Create a temporary project directory under pytest's `tmp_path`
2. Create subdirectory named "test_project"
3. Change working directory to the project using `monkeypatch.chdir()`
4. Execute `project init` command via CLI runner
5. Assert initialization succeeds (exit_code == 0)
6. Return the Path to the initialized project directory

**Behavioral Contract:**
- Each test gets isolated temporary directory (no cross-test contamination)
- Working directory is changed to project root (tests can invoke CLI commands without path manipulation)
- Project initialization uses actual CLI command (integration testing, not mocking)
- Cleanup is automatic via pytest's tmp_path mechanism

#### Scenario: Shared fixture eliminates duplication

```gherkin
Given the initialized_project fixture is defined in conftest.py
When 5 test files use the initialized_project fixture
Then each test file does NOT define its own initialized_project fixture
And each test file receives an isolated initialized project environment
And all tests pass with identical behavior to before consolidation
And changes to project initialization only require updating conftest.py
```

#### Scenario: Fixture provides isolated test environment

```gherkin
Given test_task_create.py has a test using initialized_project fixture
And test_task_show.py has a test using initialized_project fixture
When both tests run in same test session
Then each test receives a separate temporary directory
And each test's project is initialized independently
And modifications in one test do not affect the other test
And working directory changes are isolated per test
```

#### Scenario: Fixture follows pytest discovery

```gherkin
Given initialized_project fixture is defined in conftest.py
When a test file includes a test function with initialized_project parameter
Then pytest automatically discovers and injects the fixture
And no explicit import of the fixture is required
And the test file does not define a local initialized_project fixture
```

---

## MODIFIED Requirements

None. This change adds shared fixtures without modifying existing test requirements.

---

## REMOVED Requirements

None. All existing test requirements are preserved.
