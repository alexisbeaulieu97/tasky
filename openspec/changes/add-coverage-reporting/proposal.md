# Proposal: Add Coverage Reporting

**Change ID**: `add-coverage-reporting`
**Status**: Draft
**Created**: 2025-11-12
**Author**: AI Assistant
**Category**: Development / Tooling

## Overview

This proposal introduces automated test coverage reporting to the Tasky project. Currently, the project has no coverage measurement or enforcement, making it difficult to track whether the ≥80% test coverage target (defined in VISION.md) is being met. This change adds pytest-cov integration, coverage configuration, and CI/development workflow integration to enable continuous coverage monitoring.

## Problem Statement

Without automated coverage reporting:
- No visibility into which code paths are untested
- Difficult to maintain the ≥80% coverage target defined in VISION.md
- Risk of introducing untested code paths without detection
- No clear metrics for code quality and test effectiveness
- Manual coverage analysis is time-consuming and error-prone

## Why

Coverage reporting is essential for maintaining code quality and test discipline:

- **Meet Project Goals**: VISION.md explicitly targets ≥80% coverage. Without automation, this goal is unenforceable
- **Catch Gaps**: Coverage reports highlight untested code paths, enabling developers to focus testing efforts
- **Quality Gate**: CI can block PRs with insufficient coverage, preventing regressions
- **Developer Confidence**: Clear coverage metrics help developers understand test quality
- **Refactoring Safety**: Coverage data shows which code is tested before making changes

## What Changes

- Add `pytest-cov>=4.1.0` to dev dependencies in `pyproject.toml`
- Configure `[tool.coverage.run]`, `[tool.coverage.report]`, and `[tool.coverage.html]` sections in `pyproject.toml`
- Document coverage workflow and best practices
- Enable branch coverage measurement for strict quality gates
- Generate HTML reports to `htmlcov/` directory
- Enforce 80% minimum coverage threshold

## Proposed Solution

Integrate `pytest-cov` and `coverage.py` into the development workflow:

1. **Dependency**: Add `pytest-cov` to pyproject.toml dev dependencies
2. **Configuration**: Configure coverage in pyproject.toml [tool.coverage] section
3. **Dev Command**: Document coverage command for local testing
4. **CI Gate**: Set minimum threshold to 80% for enforcement
5. **Reporting**: Generate both terminal and HTML reports

### User-Facing Changes

```bash
# Run tests with coverage measurement
uv run pytest --cov=packages --cov-report=term-missing --cov-report=html

# View HTML report (generates htmlcov/ directory)
open htmlcov/index.html

# Fail if coverage below 80%
uv run pytest --cov=packages --cov-fail-under=80
```

### Configuration

Add to pyproject.toml:
```toml
[tool.coverage.run]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/conftest.py"
]
source = ["packages"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "if typing.TYPE_CHECKING:"
]
min_covered_percentage = 80

[tool.coverage.html]
directory = "htmlcov"
```

## Acceptance Criteria

1. `pytest-cov` is added to dev dependencies
2. Coverage configuration is present in pyproject.toml
3. Coverage command runs successfully with `uv run pytest --cov=packages`
4. HTML reports generate to `htmlcov/` directory
5. Terminal report shows line and branch coverage
6. Terminal report displays untested lines with `--cov-report=term-missing`
7. Coverage threshold is enforced at 80% minimum
8. Current codebase meets ≥80% coverage target
9. Documentation explains how to run and interpret coverage reports

## Non-Goals

- Coverage enforcement in CI pipeline (future PR gate)
- Codecov/Coveralls integration (external services)
- Performance profiling or optimization
- Coverage-based test selection (future enhancement)
- Coverage trends or historical reporting

## Impact

**Affected Systems**:
- Development workflow
- pyproject.toml configuration
- CI/CD pipeline (future enhancement)

**No Breaking Changes**: This is a tooling-only addition. Existing tests and code remain unchanged.

## Dependencies

This change is independent and has no dependencies on other changes or features.

## Risks and Mitigations

**Risk**: Coverage metrics might expose insufficient test coverage
**Mitigation**: If current coverage is below 80%, generate report and prioritize missing tests. Gap analysis helps identify what needs testing.

**Risk**: Branch coverage requirements might be too strict
**Mitigation**: Exclude edge cases and error paths when appropriate using `pragma: no cover` comments. Document exclusion rationale.

**Risk**: Coverage configuration might be complex
**Mitigation**: Start with simple configuration. Include clear comments explaining each setting.

## Alternatives Considered

1. **Manual coverage analysis**: Rejected because it's error-prone and non-repeatable
2. **Third-party services (Codecov)**: Rejected as unnecessary complexity for current scale
3. **Only line coverage (no branch)**: Rejected in favor of stricter branch coverage for better quality

## Implementation Notes

- Use standard `coverage.py` configuration (built-in to pytest-cov)
- Generate both terminal reports (for developer feedback) and HTML reports (for detailed analysis)
- Exclude test files and generated code automatically
- Document coverage interpretation and best practices
- Keep configuration in pyproject.toml (single source of truth)

## Related Changes

- Foundation for future CI coverage gate
- Enables data-driven decisions about test priorities
- Supports future code quality metrics

## Success Metrics

1. Coverage command executes without errors
2. Current codebase meets ≥80% threshold
3. HTML report is navigable and informative
4. Developers can quickly identify untested code
5. Configuration is simple and well-documented
