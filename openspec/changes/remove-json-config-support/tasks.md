# Tasks: Remove JSON Config Support

**Change ID**: `remove-json-config-support`
**Total Estimated Tasks**: 8
**Status**: Proposed (can be executed at any time)

## Implementation Guidance

**IMPORTANT**: This change is flexible and can be executed whenever the team decides to simplify the codebase. By the time this change is implemented:

1. **The codebase will have evolved**: Code locations, method names, and implementation details may differ from v0.x. When implementing, you MUST:
   - Search comprehensively for all JSON-related code across all packages
   - Verify each JSON code path before removal
   - Check for new JSON utility functions that didn't exist in v0.x
   - Look for JSON references in comments, examples, and docstrings

2. **Verify all JSON removal locations**:
   - `packages/tasky-projects/src/tasky_projects/config.py` - Check `ProjectConfig.from_file()` method
   - `packages/tasky-settings/src/tasky_settings/sources.py` - Check JSON source loading
   - Any JSON utility modules that may have been created
   - Example config files and documentation
   - Type hints or imports referencing JSON loaders

3. **Run exhaustive tests** after each removal to ensure:
   - No code paths accidentally exercise removed JSON code
   - TOML-only paths work correctly
   - Fallback behaviors are unchanged
   - Error messages are clear

4. **Use `rg` or `grep` to search for**:
   - `"json"` (case-insensitive)
   - `"JSON"` (uppercase)
   - `"_load_json"`
   - `"config.json"`
   - `".json"`
   - Any JSON-related imports or modules

---

## Task List

### Task 1: Audit and Map JSON Code Paths
**Estimated**: 2 hours
**Goal**: Identify all JSON-related code that must be removed

**Implementation Steps**:
1. Search for all JSON references: `rg -i "json" packages/tasky-projects/ packages/tasky-settings/`
2. Search for all `.json` file references: `rg "\.json" packages/`
3. Search for specific methods: `rg "_load_json|detect_json|json_config"` (or whatever methods exist)
4. Document all findings in a checklist:
   - [ ] Location in source code
   - [ ] Type of code (method, import, constant, utility)
   - [ ] Whether it's directly JSON-related or tangential
   - [ ] Dependencies on this code

5. Verify against known locations from v0.x:
   - [ ] `ProjectConfig.from_file()` JSON branch
   - [ ] `_load_json()` method in `tasky-projects/config.py`
   - [ ] JSON detection in `tasky-settings/sources.py`
   - [ ] JSON-related imports (`json` module, custom JSON utilities)
   - [ ] JSON test cases in test files

**Acceptance Criteria**:
- Complete inventory of all JSON-related code exists
- Each item is categorized (method, test, import, docs)
- No JSON code is missed

---

### Task 2: Remove JSON Loading Method from ProjectConfig
**Estimated**: 1 hour
**Goal**: Remove `_load_json()` or equivalent method from ProjectConfig

**Implementation Steps**:
1. Locate the JSON loading method in `packages/tasky-projects/src/tasky_projects/config.py`
2. Verify it's not called from any TOML paths
3. Remove the entire method
4. Remove any JSON-specific imports it depends on (if not needed elsewhere)
5. Run tests: `uv run pytest packages/tasky-projects/tests/test_config.py -v`
6. Verify no test failures

**Acceptance Criteria**:
- `_load_json()` method is removed
- No orphaned imports related to JSON loading
- All existing tests pass
- No test errors about missing `_load_json`

---

### Task 3: Remove JSON Detection from ProjectConfig.from_file()
**Estimated**: 1 hour
**Goal**: Simplify from_file() to only load TOML

**Implementation Steps**:
1. Locate `ProjectConfig.from_file()` method in `packages/tasky-projects/src/tasky_projects/config.py`
2. Identify all JSON detection branches (searching for `.config.json` fallback logic)
3. Remove JSON detection logic and fallback
4. Simplify to: attempt TOML, if file missing return default or raise error
5. Update docstring to remove mention of JSON legacy support
6. Run tests: `uv run pytest packages/tasky-projects/tests/test_config.py::TestProjectConfig::test_project_config_from_file -v`

**Example Before**:
```python
def from_file(cls, path: Path) -> ProjectConfig:
    toml_path = path / "config.toml"
    json_path = path / "config.json"

    if toml_path.exists():
        return cls._load_toml(toml_path)
    elif json_path.exists():
        logger.warning("Legacy JSON config detected...")
        return cls._load_json(json_path)
    else:
        return cls()
```

**Example After**:
```python
def from_file(cls, path: Path) -> ProjectConfig:
    config_path = path / "config.toml"

    if config_path.exists():
        return cls._load_toml(config_path)
    else:
        return cls()
```

**Acceptance Criteria**:
- JSON fallback branch is removed
- Method is simplified (fewer lines, single code path)
- Docstring updated
- All tests pass

---

### Task 4: Remove JSON Detection from tasky-settings Sources
**Estimated**: 1 hour
**Goal**: Remove JSON source handling from AppSettings

**Implementation Steps**:
1. Locate JSON handling in `packages/tasky-settings/src/tasky_settings/sources.py`
2. Find `ProjectConfigSource._load_config()` or equivalent method
3. Identify JSON detection and fallback logic
4. Remove JSON branches and simplify to TOML-only loading
5. Remove any migration warning logs
6. Run tests: `uv run pytest packages/tasky-settings/tests/test_sources.py -v`

**Acceptance Criteria**:
- JSON detection removed from source loader
- No warning logs about legacy JSON
- All existing tests pass
- Code is simplified

---

### Task 5: Remove JSON-Related Test Cases
**Estimated**: 1.5 hours
**Goal**: Delete all JSON-specific tests

**Implementation Steps**:
1. In `packages/tasky-projects/tests/test_config.py`:
   - Find and delete all tests matching pattern: `test_*json*` or `test_*legacy*`
   - Likely tests to remove:
     - `test_project_config_from_file_legacy_json()`
     - `test_project_config_json_to_toml_migration()`
     - `test_project_config_prefers_toml_over_json()`
     - `test_project_config_auto_detects_legacy_json_with_nonexistent_path()`
     - `test_project_config_to_file_forces_toml_extension()`
     - `test_handles_malformed_json_gracefully()`

2. In `packages/tasky-settings/tests/test_sources.py`:
   - Find and delete all JSON-specific tests:
     - `test_loads_legacy_json_config()`
     - `test_prefers_toml_over_json()`
     - `test_handles_malformed_json_gracefully()`

3. Run tests: `uv run pytest packages/tasky-projects/tests/test_config.py packages/tasky-settings/tests/test_sources.py -v`

4. Verify coverage still meets ≥80% threshold: `uv run pytest --cov=packages --cov-fail-under=80`

**Acceptance Criteria**:
- All JSON-specific test cases are deleted
- Remaining tests pass
- Coverage remains ≥80%
- No orphaned test fixtures related to JSON

---

### Task 6: Remove JSON References from ALL Code and Documentation
**Estimated**: 1 hour
**Goal**: 100% clean removal—code acts as if TOML was always the only format

**Implementation Steps**:
1. Search **entire codebase** for any JSON references: `rg -i "json|legacy|deprecated|backward.*compat" packages/ examples/ docs/`

2. Remove from **production code**:
   - All JSON examples from `examples/`
   - Any JSON schema or utility files
   - Comments mentioning JSON support or migration paths
   - Docstrings referencing JSON format or backwards compatibility
   - Type hints or imports for JSON handling

3. Remove from **documentation**:
   - Config format examples (show TOML only)
   - Any migration guides mentioning JSON
   - Stray references in README, setup guides, etc.

4. Add **ONLY to CHANGELOG**:
   ```
   ## vX.Y.Z - [date]

   ### Breaking Changes
   - Configuration now requires `.tasky/config.toml` (JSON format no longer supported).
     Users with legacy `.tasky/config.json` files must rename and convert to TOML format.
   ```
   This is the **only place** JSON removal is mentioned—nowhere else in the codebase.

5. **Final validation** - Zero tolerance check:
   - `rg -i "json" packages/` (should find nothing in production code)
   - `rg "legacy" packages/tasky-projects/ packages/tasky-settings/` (should find nothing)
   - `rg "backward" packages/` (should find nothing)
   - `rg "deprecat" packages/tasky-projects/ packages/tasky-settings/` (should find nothing)

**Acceptance Criteria**:
- **ZERO** JSON references in production code
- **ZERO** deprecation/legacy/backwards-compat language in production code
- **ZERO** comments explaining why JSON was removed
- Code reads as if TOML-only design from day one
- CHANGELOG documents breaking change (only location mentioning JSON removal)
- All tests pass
- No orphaned imports or utilities

---

### Task 7: Remove JSON Imports and Dependencies
**Estimated**: 30 minutes
**Goal**: Clean up unused imports and dependencies

**Implementation Steps**:
1. Check if `json` module is imported anywhere it's no longer needed:
   - `rg "^import json|^from json" packages/`

2. Remove unused imports from:
   - `tasky-projects/config.py`
   - `tasky-settings/sources.py`
   - Any JSON utility modules

3. Check if any JSON parsing libraries can be removed from dependencies (unlikely, but check):
   - Verify `tomli`, `tomli_w` are still needed for TOML
   - Check `pyproject.toml` for any JSON-specific dependencies that can be dropped

4. Run linter to ensure no unused imports: `uv run ruff check --fix`

**Acceptance Criteria**:
- No unused `json` imports
- All necessary TOML imports present
- Linter passes with no issues
- No broken imports

---

### Task 8: Final Validation—100% Clean Verification
**Estimated**: 1.5 hours
**Goal**: Confirm code is 100% clean (TOML-only, zero JSON traces)

**Implementation Steps**:

1. **Comprehensive code audit**:
   ```bash
   # Zero tolerance searches across all production code
   rg -i "json" packages/tasky-projects/ packages/tasky-settings/ packages/tasky-storage/
   rg "legacy" packages/tasky-projects/ packages/tasky-settings/
   rg "backward" packages/
   rg "deprecat" packages/tasky-projects/ packages/tasky-settings/
   rg "migration" packages/tasky-projects/ packages/tasky-settings/ packages/tasky-cli/
   rg "_load_json|_parse_json|from_json" packages/
   ```
   **Expected result**: All searches return ZERO matches in `packages/` directories

2. Run full test suite: `uv run pytest`
   - Should pass (with fewer tests due to JSON test removal)
   - No failures, no JSON-related errors

3. Run coverage validation: `uv run pytest --cov=packages --cov-fail-under=80`
   - Must meet ≥80% threshold

4. Run linter: `uv run ruff check --fix`
   - No errors or warnings

5. CLI smoke tests:
   ```bash
   uv run tasky --help  # Should work
   uv run tasky project init --name test  # Should create .tasky/config.toml
   ```

6. **Verify error behavior** (ensure code is TOML-only):
   - Manually create a test directory without `.tasky/config.toml`
   - Run any tasky command
   - Verify error message: "Config file not found: .tasky/config.toml" (no mention of JSON)

7. **Code review checklist**:
   - [ ] No JSON imports (`import json`, `from json`)
   - [ ] No JSON-related comments or docstrings
   - [ ] No utility functions for JSON
   - [ ] `ProjectConfig.from_file()` only reads TOML
   - [ ] Config loading code is straightforward (no branching)
   - [ ] No deprecation warnings anywhere
   - [ ] No backwards-compatibility paths in code

**Acceptance Criteria**:
- ✅ All code audit searches return ZERO matches
- ✅ All tests pass (reduced count from JSON removal)
- ✅ Coverage ≥80%
- ✅ Linter clean
- ✅ CLI works correctly
- ✅ Error messages are generic (no JSON mentions)
- ✅ Code review checklist 100% complete
- ✅ **Ready for code review**: Change is 100% clean as if TOML was always the only format

---

## Dependencies and Sequencing

```
Task 1 (Audit)
├── Task 2 (Remove _load_json method)
├── Task 3 (Remove JSON detection from from_file)
├── Task 4 (Remove JSON detection from sources)
└── Task 5 (Remove JSON test cases)
    ├── Task 6 (Remove JSON from docs)
    ├── Task 7 (Remove JSON imports)
    └── Task 8 (Full validation)
```

**Execution Order**:
1. Task 1 first (understand what you're removing)
2. Tasks 2-4 in parallel or sequence (all remove code)
3. Task 5 after code removal (tests will now be out of sync)
4. Tasks 6-7 in parallel (documentation cleanup)
5. Task 8 last (final validation)

---

## Success Criteria (Overall)

- ✅ Zero JSON-related code in production (checked via `rg`)
- ✅ All tests pass with ≥80% coverage
- ✅ Linter passes with no errors
- ✅ CLI smoke tests pass
- ✅ Documentation reflects TOML-only status
- ✅ Release notes document breaking change and migration path
- ✅ No orphaned JSON-related comments or docstrings
