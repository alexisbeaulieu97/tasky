# Implementation Tasks: Implement Project List Command

This document outlines the ordered implementation tasks for adding the `tasky project list` command. Tasks are designed to deliver user-visible progress incrementally with validation at each step.

## Task Checklist

### Phase 1: Project Locator Service (Foundation)

- [ ] **Task 1.1**: Create project locator module
  - Create `packages/tasky-projects/src/tasky_projects/locator.py`
  - Define `ProjectLocation` dataclass with fields: path, backend, storage_path
  - Implement `find_projects_upward(start_dir: Path) -> List[ProjectLocation]`
  - Search from `start_dir` upward to filesystem root, stopping at home directory
  - Return list of found projects sorted by path
  - **Validation**: Module imports without errors

- [ ] **Task 1.2**: Implement recursive project search
  - Add `find_projects_recursive(root_dir: Path) -> List[ProjectLocation]`
  - Use `os.walk()` to traverse entire tree
  - Collect all `.tasky/config.toml` files
  - Return list of found projects sorted by path
  - Handle permission errors gracefully
  - **Validation**: Method compiles and type-checks

- [ ] **Task 1.3**: Parse project configuration files
  - Implement `_load_project_config(config_path: Path) -> dict`
  - Read and parse `.tasky/config.toml`
  - Extract `storage.backend` and `storage.path` fields
  - Handle missing or malformed config files
  - Return configuration dictionary
  - **Validation**: Successfully parses valid config files

- [ ] **Task 1.4**: Write unit tests for locator
  - Create `packages/tasky-projects/tests/test_locator.py`
  - Test `find_projects_upward()` finds parent directories
  - Test `find_projects_recursive()` finds nested projects
  - Test sorting of results
  - Test handling of missing config files
  - Test permission error handling
  - **Validation**: Run `uv run pytest packages/tasky-projects/tests/test_locator.py -v`

### Phase 2: CLI Integration

- [ ] **Task 2.1**: Add `project list` command
  - Update `packages/tasky-cli/src/tasky_cli/commands/projects.py`
  - Add `list_command()` function
  - Add `--recursive` boolean flag (default: False)
  - Add `--root` string option for custom search directory (default: current directory)
  - **Validation**: Run `uv run tasky project list --help` and verify options appear

- [ ] **Task 2.2**: Implement project discovery logic
  - Call `find_projects_upward()` or `find_projects_recursive()` based on flags
  - Use `--root` value or current directory as starting point
  - Collect results from locator service
  - **Validation**: Command runs without errors

- [ ] **Task 2.3**: Format and display results
  - Display each project with: path, backend, storage path
  - Show count: "Found N projects" or "Found 1 project"
  - Use consistent table or line-based formatting
  - Sort results by path for consistency
  - **Validation**: Manual testing shows clear, readable output

- [ ] **Task 2.4**: Handle empty results gracefully
  - Display helpful message when no projects found
  - Message should suggest: "No projects found. Run 'tasky project init' to create one."
  - Exit with status code 0 (success)
  - **Validation**: Manual testing of no-results case

### Phase 3: Testing and Validation

- [ ] **Task 3.1**: Add CLI integration tests
  - Create `packages/tasky-cli/tests/test_project_list.py`
  - Test listing projects with upward search (default)
  - Test listing with `--recursive` flag
  - Test listing from custom `--root` directory
  - Test no projects found scenario
  - Test output formatting and count display
  - **Validation**: Run `uv run pytest packages/tasky-cli/tests/test_project_list.py -v`

- [ ] **Task 3.2**: End-to-end scenario testing
  - Create test fixture with multiple .tasky directories
  - Initialize projects at various nesting levels
  - Test discovering all projects with `--recursive`
  - Test discovering projects upward from nested directory
  - **Validation**: All scenarios pass

- [ ] **Task 3.3**: Run full test suite
  - Run `uv run pytest` across all packages
  - Address any failures or regressions
  - Verify test coverage meets ≥80% target
  - **Validation**: All tests pass with no regressions

### Phase 4: Final Validation

- [ ] **Task 4.1**: Manual smoke testing
  - Initialize projects in different directories
  - Test `tasky project list` from various locations
  - Test `--recursive` flag behavior
  - Test `--root` flag with absolute paths
  - Verify output is clear and correct
  - **Validation**: All variations work correctly

- [ ] **Task 4.2**: Code quality checks
  - Run `uv run ruff check --fix`
  - Run `uv run ruff format`
  - Ensure no linting errors
  - Verify type hints are complete
  - **Validation**: Code passes all quality checks

- [ ] **Task 4.3**: Documentation and help text
  - Update help text with clear descriptions of flags
  - Add usage examples to help output
  - Document behavior in code comments
  - **Validation**: Help text is clear and accurate

## Notes

- **Dependencies**: Tasks must be completed sequentially within each phase
- **Parallelization**: Phase 1 can be done before CLI work once interface is defined
- **Testing Strategy**: Test at each layer (unit → integration → end-to-end)
- **Rollback**: Each task is independently reversible if issues arise

## Estimated Duration

- Phase 1: 1 hour
- Phase 2: 45 minutes
- Phase 3: 45 minutes
- Phase 4: 30 minutes

**Total**: ~3 hours
