# Tasks: Hierarchical Configuration System

## Phase 1: Settings Models (tasky-settings)

1. [ ] Update `packages/tasky-settings/pyproject.toml` to add `pydantic-settings>=2.5.0` dependency
2. [ ] Create `packages/tasky-settings/src/tasky_settings/models.py` module
3. [ ] Implement `LoggingSettings` model with `verbosity` and `format` fields
4. [ ] Implement `TaskDefaultsSettings` model with `priority` and `status` fields
5. [ ] Implement `AppSettings` model inheriting from `BaseSettings` with proper config
6. [ ] Add field validation (ranges, literal values) to all settings models
7. [ ] Configure `AppSettings` with `env_prefix="TASKY_"` and `env_nested_delimiter="__"`
8. [ ] Export settings models from `packages/tasky-settings/src/tasky_settings/__init__.py`

## Phase 2: Custom TOML Sources (tasky-settings)

9. [ ] Create `packages/tasky-settings/src/tasky_settings/sources.py` module
10. [ ] Implement `TomlConfigSource` base class extending `PydanticBaseSettingsSource`
11. [ ] Implement `__call__()` method to load and parse TOML files
12. [ ] Handle missing files gracefully (return empty dict)
13. [ ] Handle malformed TOML gracefully (return empty dict, optionally log warning)
14. [ ] Implement `GlobalConfigSource` class for `~/.tasky/config.toml`
15. [ ] Implement `ProjectConfigSource` class for `.tasky/config.toml`
16. [ ] Add `project_root` parameter to `ProjectConfigSource` with `Path.cwd()` default

## Phase 3: Settings Factory (tasky-settings)

17. [ ] Create `get_settings()` function in `packages/tasky-settings/src/tasky_settings/__init__.py`
18. [ ] Add `project_root: Path | None` parameter to factory
19. [ ] Add `cli_overrides: dict[str, Any] | None` parameter to factory
20. [ ] Implement `settings_customise_sources` function defining source precedence
21. [ ] Configure source order: init → global → project → env → cli_overrides
22. [ ] Return fully configured `AppSettings` instance
23. [ ] Export `get_settings` from package `__init__.py`

## Phase 4: Logging Integration

24. [ ] Update `packages/tasky-logging/src/tasky_logging/config.py` signature
25. [ ] Change `configure_logging()` to accept `settings: LoggingSettings` parameter
26. [ ] Remove individual `verbosity` and `format_style` parameters
27. [ ] Add TYPE_CHECKING import for `LoggingSettings` from tasky_settings.models
28. [ ] Update logging level mapping to use `settings.verbosity`
29. [ ] Update format selection to use `settings.format`
30. [ ] Add support for "minimal" format (level + message only)
31. [ ] Add placeholder for "json" format (can be basic for now)

## Phase 5: CLI Integration

32. [ ] Update `packages/tasky-cli/pyproject.toml` to add `tasky-settings` dependency
33. [ ] Import `get_settings` in `packages/tasky-cli/src/tasky_cli/__init__.py`
34. [ ] Update `main_callback()` to build `cli_overrides` dict from verbose count
35. [ ] Call `get_settings(cli_overrides=...)` in main callback
36. [ ] Pass `settings.logging` to `configure_logging()`
37. [ ] Store settings in Typer context for commands: `ctx.obj["settings"] = settings`
38. [ ] Update callback docstring to mention settings system

## Phase 6: Unit Tests (tasky-settings)

39. [ ] Create `packages/tasky-settings/tests/test_models.py`
40. [ ] Test `LoggingSettings` validation (valid and invalid verbosity values)
41. [ ] Test `TaskDefaultsSettings` validation
42. [ ] Test `AppSettings` composition and env var prefix
43. [ ] Create `packages/tasky-settings/tests/test_sources.py`
44. [ ] Test `TomlConfigSource` loads valid TOML files
45. [ ] Test `TomlConfigSource` handles missing files gracefully
46. [ ] Test `TomlConfigSource` handles malformed TOML gracefully
47. [ ] Test `GlobalConfigSource` uses correct path (`~/.tasky/config.toml`)
48. [ ] Test `ProjectConfigSource` uses correct path relative to project root

## Phase 7: Integration Tests (tasky-settings)

49. [ ] Create `packages/tasky-settings/tests/test_hierarchy.py`
50. [ ] Test precedence: project config overrides global config
51. [ ] Test precedence: env vars override file configs
52. [ ] Test precedence: cli_overrides override everything
53. [ ] Test partial config merging (project overrides only some fields)
54. [ ] Test missing config files use model defaults
55. [ ] Test invalid config values raise helpful validation errors

## Phase 8: Update Logging Tests

56. [ ] Update `packages/tasky-logging/tests/test_logging.py`
57. [ ] Modify `test_configure_logging_*` tests to pass `LoggingSettings` objects
58. [ ] Add test for configure_logging with settings object
59. [ ] Verify backward compatibility (logging works without settings package)

## Phase 9: Update CLI Tests

60. [ ] Update `packages/tasky-cli/tests/test_verbosity.py` if needed
61. [ ] Add test verifying settings are loaded in CLI callback
62. [ ] Test that CLI flags create proper override dictionaries
63. [ ] Verify logging is configured from settings

## Phase 10: Documentation and Examples

64. [ ] Create example `~/.tasky/config.toml` with commented sections
65. [ ] Create example `.tasky/config.toml` with common project overrides
66. [ ] Update `packages/tasky-settings/README.md` with usage examples
67. [ ] Document precedence rules in README
68. [ ] Document environment variable naming (`TASKY_LOGGING__VERBOSITY`)
69. [ ] Add examples of CLI flag overrides

## Phase 11: Validation and Cleanup

70. [ ] Run `uv run pytest` to ensure all tests pass
71. [ ] Run `uv run ruff check --fix` to ensure code quality
72. [ ] Manually test: create `~/.tasky/config.toml` with verbosity setting
73. [ ] Manually test: verify verbosity from global config works
74. [ ] Manually test: create `.tasky/config.toml` with different verbosity
75. [ ] Manually test: verify project config overrides global
76. [ ] Manually test: verify CLI `-v` flag overrides configs
77. [ ] Manually test: set `TASKY_LOGGING__VERBOSITY=2` and verify it works
78. [ ] Run `openspec validate add-hierarchical-configuration --strict`
79. [ ] Resolve any validation issues
80. [ ] Review all code for consistency and quality

## Validation Checklist

- [ ] Global config (`~/.tasky/config.toml`) sets default logging verbosity
- [ ] Project config (`.tasky/config.toml`) overrides global for that project
- [ ] Environment variable `TASKY_LOGGING__VERBOSITY` overrides file configs
- [ ] CLI `-v` and `-vv` flags override all other sources
- [ ] Invalid config values show helpful validation errors
- [ ] Missing config files don't cause errors (use defaults)
- [ ] All tests pass
- [ ] Code passes ruff checks
- [ ] OpenSpec validation passes with --strict flag
