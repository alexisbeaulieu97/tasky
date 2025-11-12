# Tasks: Hierarchical Configuration System

## Phase 1: Settings Models (tasky-settings)

1. [x] Update `packages/tasky-settings/pyproject.toml` to add `pydantic-settings>=2.5.0` dependency
2. [x] Create `packages/tasky-settings/src/tasky_settings/models.py` module
3. [x] Implement `LoggingSettings` model with `verbosity` and `format` fields
4. [x] Implement `TaskDefaultsSettings` model with `priority` and `status` fields
5. [x] Implement `AppSettings` model inheriting from `BaseSettings` with proper config
6. [x] Add field validation (ranges, literal values) to all settings models
7. [x] Configure `AppSettings` with `env_prefix="TASKY_"` and `env_nested_delimiter="__"`
8. [x] Export settings models from `packages/tasky-settings/src/tasky_settings/__init__.py`

## Phase 2: Custom TOML Sources (tasky-settings)

9. [x] Create `packages/tasky-settings/src/tasky_settings/sources.py` module
10. [x] Implement `TomlConfigSource` base class extending `PydanticBaseSettingsSource`
11. [x] Implement `__call__()` method to load and parse TOML files
12. [x] Handle missing files gracefully (return empty dict)
13. [x] Handle malformed TOML gracefully (return empty dict, optionally log warning)
14. [x] Implement `GlobalConfigSource` class for `~/.tasky/config.toml`
15. [x] Implement `ProjectConfigSource` class for `.tasky/config.toml`
16. [x] Add `project_root` parameter to `ProjectConfigSource` with `Path.cwd()` default

## Phase 3: Settings Factory (tasky-settings)

17. [x] Create `get_settings()` function in `packages/tasky-settings/src/tasky_settings/__init__.py`
18. [x] Add `project_root: Path | None` parameter to factory
19. [x] Add `cli_overrides: dict[str, Any] | None` parameter to factory
20. [x] Implement `settings_customise_sources` function defining source precedence
21. [x] Configure source order: init → global → project → env → cli_overrides
22. [x] Return fully configured `AppSettings` instance
23. [x] Export `get_settings` from package `__init__.py`

## Phase 4: Logging Integration

24. [x] Update `packages/tasky-logging/src/tasky_logging/config.py` signature
25. [x] Change `configure_logging()` to accept `settings: LoggingSettings` parameter
26. [x] Remove individual `verbosity` and `format_style` parameters
27. [x] Add TYPE_CHECKING import for `LoggingSettings` from tasky_settings.models
28. [x] Update logging level mapping to use `settings.verbosity`
29. [x] Update format selection to use `settings.format`
30. [x] Add support for "minimal" format (level + message only)
31. [x] Add placeholder for "json" format (can be basic for now)

## Phase 5: CLI Integration

32. [x] Update `packages/tasky-cli/pyproject.toml` to add `tasky-settings` dependency
33. [x] Import `get_settings` in `packages/tasky-cli/src/tasky_cli/__init__.py`
34. [x] Update `main_callback()` to build `cli_overrides` dict from verbose count
35. [x] Call `get_settings(cli_overrides=...)` in main callback
36. [x] Pass `settings.logging` to `configure_logging()`
37. [x] Store settings in Typer context for commands: `ctx.obj["settings"] = settings`
38. [x] Update callback docstring to mention settings system

## Phase 6: Unit Tests (tasky-settings)

39. [x] Create `packages/tasky-settings/tests/test_models.py`
40. [x] Test `LoggingSettings` validation (valid and invalid verbosity values)
41. [x] Test `TaskDefaultsSettings` validation
42. [x] Test `AppSettings` composition and env var prefix
43. [x] Create `packages/tasky-settings/tests/test_sources.py`
44. [x] Test `TomlConfigSource` loads valid TOML files
45. [x] Test `TomlConfigSource` handles missing files gracefully
46. [x] Test `TomlConfigSource` handles malformed TOML gracefully
47. [x] Test `GlobalConfigSource` uses correct path (`~/.tasky/config.toml`)
48. [x] Test `ProjectConfigSource` uses correct path relative to project root

## Phase 7: Integration Tests (tasky-settings)

49. [x] Create `packages/tasky-settings/tests/test_hierarchy.py`
50. [x] Test precedence: project config overrides global config
51. [x] Test precedence: env vars override file configs
52. [x] Test precedence: cli_overrides override everything
53. [x] Test partial config merging (project overrides only some fields)
54. [x] Test missing config files use model defaults
55. [x] Test invalid config values raise helpful validation errors

## Phase 8: Update Logging Tests

56. [x] Update `packages/tasky-logging/tests/test_logging.py`
57. [x] Modify `test_configure_logging_*` tests to pass `LoggingSettings` objects
58. [x] Add test for configure_logging with settings object
59. [x] Verify backward compatibility (logging works without settings package)

## Phase 9: Update CLI Tests

60. [x] Update `packages/tasky-cli/tests/test_verbosity.py` if needed
61. [x] Add test verifying settings are loaded in CLI callback
62. [x] Test that CLI flags create proper override dictionaries
63. [x] Verify logging is configured from settings

## Phase 10: Documentation and Examples

64. [x] Create example `~/.tasky/config.toml` with commented sections
65. [x] Create example `.tasky/config.toml` with common project overrides
66. [x] Update `packages/tasky-settings/README.md` with usage examples
67. [x] Document precedence rules in README
68. [x] Document environment variable naming (`TASKY_LOGGING__VERBOSITY`)
69. [x] Add examples of CLI flag overrides

## Phase 11: Validation and Cleanup

70. [x] Run `uv run pytest` to ensure all tests pass
71. [x] Run `uv run ruff check --fix` to ensure code quality
72. [x] Manually test: create `~/.tasky/config.toml` with verbosity setting
73. [x] Manually test: verify verbosity from global config works
74. [x] Manually test: create `.tasky/config.toml` with different verbosity
75. [x] Manually test: verify project config overrides global
76. [x] Manually test: verify CLI `-v` flag overrides configs
77. [x] Manually test: set `TASKY_LOGGING__VERBOSITY=2` and verify it works
78. [x] Run `openspec validate add-hierarchical-configuration --strict`
79. [x] Resolve any validation issues
80. [x] Review all code for consistency and quality

## Validation Checklist

- [x] Global config (`~/.tasky/config.toml`) sets default logging verbosity
- [x] Project config (`.tasky/config.toml`) overrides global for that project
- [x] Environment variable `TASKY_LOGGING__VERBOSITY` overrides file configs
- [x] CLI `-v` and `-vv` flags override all other sources
- [x] Invalid config values show helpful validation errors
- [x] Missing config files don't cause errors (use defaults)
- [x] All tests pass
- [x] Code passes ruff checks
- [x] OpenSpec validation passes with --strict flag
