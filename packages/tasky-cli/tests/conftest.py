"""Shared fixtures for tasky-cli tests.

This module provides common fixtures used across the test suite:
- runner: A Typer CLI test runner for invoking commands
- initialized_project: A temporary project directory with initialized .tasky/ structure
"""

from pathlib import Path

import pytest
from tasky_cli.commands.projects import project_app
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def initialized_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an initialized project directory for CLI tests."""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    monkeypatch.chdir(project_path)

    result = CliRunner().invoke(project_app, ["init"])
    assert result.exit_code == 0

    return project_path

