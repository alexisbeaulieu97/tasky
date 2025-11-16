# Design: Consolidate Test Fixtures

## Problem Analysis

### Current State
**Fixture Duplication**:
- `initialized_project` fixture duplicated in 5 files
- Each copy: 13 lines of identical code
- Total duplication: 52 lines across codebase

**Files with duplicate `initialized_project`**:
1. `test_task_create.py` (lines 12-25)
2. `test_task_show.py` (lines 12-25)
3. `test_task_update.py` (lines 14-27)
4. `test_import_export.py` (lines 19-32)
5. `test_task_list_format.py` (lines 12-25)

**Existing Infrastructure**:
- `conftest.py` already exists with shared `runner` fixture
- Pytest automatically discovers fixtures in `conftest.py`
- Some test files already use shared `runner` fixture, demonstrating the pattern works

### Duplication Impact
1. **Maintenance**: Changes to project initialization require 5 updates
2. **Drift risk**: Fixtures may diverge if one is updated and others aren't
3. **Readability**: Each test file includes 13 lines of boilerplate
4. **Discoverability**: New contributors may not know which fixture implementation is "canonical"

## Design Decision: Consolidation Strategy

### Option 1: Simple Consolidation (SELECTED)
Move exact current fixture to `conftest.py` with zero behavioral changes.

**Pros**:
- Minimal risk (identical behavior guaranteed)
- Quick to implement and validate
- Removes duplication immediately
- Easy to enhance later if needed

**Cons**:
- Doesn't add new test capabilities
- May require future enhancement for multi-backend tests

### Option 2: Enhanced Fixture with Parameters (DEFERRED)
Create parameterized fixture supporting multiple backends and pre-populated scenarios.

**Pros**:
- More flexible for future test scenarios
- Could support backend-agnostic tests

**Cons**:
- Higher initial complexity
- Risk of over-engineering for current needs
- Can be added later if needed

**Decision**: Start with Option 1 (simple consolidation), add enhancements in future change if multi-backend testing becomes priority.

## Fixture Design

### `initialized_project` Fixture (Shared Implementation)

**Location**: `packages/tasky-cli/tests/conftest.py`

**Implementation**:
```python
@pytest.fixture
def initialized_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an initialized project directory.

    This fixture:
    - Creates a temporary project directory
    - Changes working directory to the project
    - Runs `tasky project init` to initialize the project
    - Returns the project path for use in tests

    The fixture ensures each test runs in an isolated project environment
    with a clean initialized state.

    Args:
        tmp_path: Pytest's temporary directory fixture
        monkeypatch: Pytest's monkeypatch fixture for changing working directory

    Returns:
        Path to the initialized project directory
    """
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    # Initialize project
    runner = CliRunner()
    result = runner.invoke(project_app, ["init"])
    assert result.exit_code == 0

    return project_path
```

**Dependencies**:
- `tmp_path`: Built-in pytest fixture
- `monkeypatch`: Built-in pytest fixture
- `CliRunner`: Already imported in conftest.py
- `project_app`: Need to add import from `tasky_cli.commands.projects`

**Behavioral Contract**:
- Creates isolated temp directory per test
- Initializes tasky project with `project init` command
- Changes working directory to project (tests expect to run from project root)
- Returns project path for tests that need explicit path reference
- Cleans up automatically (pytest handles tmp_path cleanup)

### Future Enhancement Opportunities (Not in This Change)

**Multi-backend support** (deferred):
```python
@pytest.fixture(params=["json", "sqlite"])
def initialized_project_all_backends(tmp_path, monkeypatch, request):
    """Test against all storage backends."""
    backend = request.param
    # Initialize with specific backend...
```

**Pre-populated fixtures** (deferred):
```python
@pytest.fixture
def project_with_tasks(initialized_project):
    """Project with 3 sample tasks."""
    # Create tasks...
```

## Migration Strategy

### Phase 1: Add Shared Fixture
1. Add `initialized_project` to `conftest.py`
2. Add necessary import: `from tasky_cli.commands.projects import project_app`
3. Run tests → verify pytest discovers fixture

### Phase 2: Remove Duplicates One File at a Time
For each of the 5 test files:
1. Remove local `initialized_project` fixture definition
2. Run tests for that specific file: `uv run pytest packages/tasky-cli/tests/test_task_create.py -v`
3. Verify all tests pass with identical behavior
4. Move to next file

**Order of removal** (simplest to most complex):
1. `test_task_create.py` (simplest task operations)
2. `test_task_show.py`
3. `test_task_update.py`
4. `test_task_list_format.py`
5. `test_import_export.py` (most complex, includes import/export scenarios)

### Phase 3: Final Validation
1. Run full test suite: `uv run pytest packages/tasky-cli/tests/ -v`
2. Verify all 577 tests pass
3. Run linting: `uv run ruff check --fix`
4. Run type checking: `uv run pyright`

## Testing Strategy

### Behavioral Equivalence Verification
**For each test file**:
- Run tests before removing duplicate fixture → capture output
- Remove duplicate fixture
- Run tests after → verify identical output
- Verify exit codes unchanged
- Verify test count unchanged

**Full test suite validation**:
- All 577 tests must pass after consolidation
- Zero new linting or type errors
- Coverage maintained at ≥80%

### Rollback Plan
If issues arise:
1. Revert changes to specific test file
2. Shared fixture remains in conftest.py (no harm)
3. File reverts to using local fixture
4. Investigate root cause before re-attempting

## Success Criteria

✅ `initialized_project` fixture exists in `conftest.py`
✅ All 5 duplicate definitions removed from test files
✅ All 577 tests pass with zero modifications to test logic
✅ Zero new linting or type errors
✅ Coverage maintained at ≥80%
✅ ~52 lines of duplicate code removed
✅ Future project initialization changes only require one update location
