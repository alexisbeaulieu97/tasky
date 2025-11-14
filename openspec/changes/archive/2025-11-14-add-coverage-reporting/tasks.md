# Implementation Tasks: Add Coverage Reporting

This document outlines the ordered implementation tasks for adding test coverage reporting. Tasks are designed to establish coverage infrastructure incrementally with validation at each step.

## Task Checklist

### Phase 1: Dependency Configuration

- [x] **Task 1.1**: Add pytest-cov to dev dependencies
  - Update `pyproject.toml` in root
  - Add `pytest-cov>=4.1.0` to `[dependency-groups] dev` section
  - **Validation**: Run `uv sync` and verify pytest-cov is installed

- [x] **Task 1.2**: Configure coverage.py in pyproject.toml
  - Add `[tool.coverage.run]` section:
    - Set `branch = true` for branch coverage
    - Set `source = ["packages"]` to measure only src code
    - Configure `omit` to exclude test files and generated code
  - Add `[tool.coverage.report]` section:
    - Configure `exclude_lines` for non-testable patterns
    - Set `fail_under = 80`
  - Add `[tool.coverage.html]` section:
    - Set `directory = "htmlcov"`
  - **Validation**: pyproject.toml is valid TOML with no syntax errors

- [x] **Task 1.3**: Verify configuration loads correctly
  - Run `uv run python -m coverage --version`
  - Run `uv run python -m coverage --help`
  - Verify configuration is recognized
  - **Validation**: Both commands execute successfully

### Phase 2: Coverage Measurement

- [x] **Task 2.1**: Run pytest with coverage measurement
  - Execute `uv run pytest --cov=packages --cov-report=term-missing --cov-report=html`
  - Observe coverage output in terminal
  - Verify HTML report is generated in `htmlcov/` directory
  - **Validation**: Command completes successfully with coverage summary

- [x] **Task 2.2**: Analyze coverage report
  - Review terminal output for overall coverage percentage
  - Open `htmlcov/index.html` in browser
  - Navigate through package coverage details
  - Identify any packages below 80% threshold
  - **Validation**: Coverage report is navigable and shows package-level details

- [x] **Task 2.3**: Verify branch coverage is measured
  - Check terminal report shows both "line" and "branch" coverage percentages
  - Confirm HTML report includes branch coverage details
  - Identify untested branches
  - **Validation**: Both line and branch coverage are visible in reports

### Phase 3: Threshold Enforcement

- [x] **Task 3.1**: Test coverage threshold enforcement
  - Run `uv run pytest --cov=packages --cov-fail-under=80`
  - Verify command succeeds if coverage ≥80%
  - Verify command fails if coverage <80%
  - **Validation**: Exit codes match expected behavior (0 for pass, 1 for fail)

- [x] **Task 3.2**: Fix coverage gaps if needed
  - Identify packages or modules below 80%
  - Analyze untested code paths
  - Add tests to bring coverage to target
  - Re-run coverage until ≥80% is achieved
  - **Validation**: Full test suite passes and coverage ≥80%

- [x] **Task 3.3**: Verify complete test coverage
  - Run full test suite: `uv run pytest`
  - Run coverage measurement: `uv run pytest --cov=packages --cov-fail-under=80`
  - Confirm both pass without errors
  - **Validation**: All tests pass AND coverage threshold met

### Phase 4: Documentation and Best Practices

- [x] **Task 4.1**: Create coverage documentation
  - Update `CLAUDE.md` or README with coverage workflow
  - Document how to run coverage command
  - Explain coverage report interpretation
  - Include examples of viewing HTML report
  - **Validation**: Documentation is clear and complete

- [x] **Task 4.2**: Document coverage exceptions
  - Document use of `pragma: no cover` for legitimate exclusions
  - Provide examples of when to exclude lines
  - Explain branch exclusion guidelines
  - **Validation**: Examples and guidelines are clear

- [x] **Task 4.3**: Add coverage check to development workflow
  - Update any development scripts or makefiles
  - Ensure coverage runs as part of standard workflow
  - Document in contributing guidelines if applicable
  - **Validation**: Coverage workflow is documented

### Phase 5: Validation and Quality

- [x] **Task 5.1**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Verify no linting errors from coverage changes
  - **Validation**: Code passes all quality checks

- [x] **Task 5.2**: Full test suite execution
  - Run `uv run pytest` across all packages
  - Verify all 379+ tests pass
  - No regressions from coverage setup
  - **Validation**: All tests pass (0 failures, 0 errors)

- [x] **Task 5.3**: Final coverage verification
  - Run `uv run pytest --cov=packages --cov-fail-under=80`
  - Confirm ≥80% coverage target achieved
  - Verify HTML report generates correctly
  - **Validation**: Coverage ≥80% and report is valid

## Notes

- **Dependencies**: Tasks must be completed sequentially within each phase
- **Parallelization**: Phases 1 and 2 can overlap once dependencies are installed
- **Testing Strategy**: Measure, analyze, fix gaps, enforce threshold
- **Cleanup**: Exclude `htmlcov/` directory from version control (typically git-ignored)
- **CI Integration**: This phase focuses on local development; CI integration is a future enhancement

## Configuration Details

### Branch Coverage

Branch coverage measures whether all conditional branches are executed:
```python
if condition:  # Branch 1: True path
    do_something()
else:          # Branch 2: False path
    do_other()
```

Both branches must be tested for 100% branch coverage.

### Omit Patterns

Test files are omitted to avoid measuring test code itself:
- `*/tests/*` - Test directories
- `*/test_*.py` - Individual test files
- `*/__init__.py` - Package init files (usually minimal)
- `*/conftest.py` - Pytest configuration

### Exclude Lines

Non-testable patterns that can be safely excluded:
- `pragma: no cover` - Explicit exclusion marker
- `raise NotImplementedError` - Placeholder code
- `if __name__ == "__main__":` - Script guard
- `if TYPE_CHECKING:` - Type-checking imports

## Estimated Duration

- Phase 1: 15 minutes (dependency setup)
- Phase 2: 30 minutes (measurement and analysis)
- Phase 3: 30 minutes (threshold enforcement and fixes)
- Phase 4: 20 minutes (documentation)
- Phase 5: 15 minutes (validation)

**Total**: ~2 hours

## Troubleshooting

### Issue: Coverage below 80%

**Solution**: Identify untested modules and add tests:
```bash
# Find modules with low coverage
uv run pytest --cov=packages --cov-report=term-missing | grep -E "< 80%"
```

### Issue: HTML report doesn't generate

**Solution**: Ensure htmlcov directory is writable:
```bash
rm -rf htmlcov/
uv run pytest --cov=packages --cov-report=html
```

### Issue: Coverage threshold check fails in CI

**Solution**: Address coverage gaps before pushing:
```bash
uv run pytest --cov=packages --cov-fail-under=80
```

## Related Commands

```bash
# Run pytest with all coverage options
uv run pytest --cov=packages --cov-report=term-missing --cov-report=html --cov-fail-under=80

# Run coverage separately (advanced)
uv run coverage run -m pytest
uv run coverage report
uv run coverage html

# Clean up coverage data
rm -rf .coverage htmlcov/
```
