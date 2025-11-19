"""Integration tests for CLI hooks."""

import re
from unittest.mock import patch

from tasky_cli import app
from tasky_hooks.dispatcher import get_dispatcher
from typer.testing import CliRunner

runner = CliRunner()


def test_verbose_hooks_flag() -> None:
    """Test that --verbose-hooks flag enables hook output."""
    # Clear existing handlers
    dispatcher = get_dispatcher()
    dispatcher.reset()

    with (
        runner.isolated_filesystem(),
        patch(
            "tasky_cli.commands.tasks.load_user_hooks",
        ),
    ):
        # Initialize project first to ensure storage is ready
        init_result = runner.invoke(app, ["project", "init"])
        assert init_result.exit_code == 0

        result = runner.invoke(
            app,
            ["task", "--verbose-hooks", "create", "Test Task", "Details"],
        )

    assert result.exit_code == 0
    assert "Hook: task_created fired" in result.stdout
    assert "Task: Test Task" in result.stdout


def test_no_verbose_hooks_flag() -> None:
    """Test that hook output is hidden without flag."""
    # Clear existing handlers
    dispatcher = get_dispatcher()
    dispatcher.reset()

    with (
        runner.isolated_filesystem(),
        patch(
            "tasky_cli.commands.tasks.load_user_hooks",
        ),
    ):
        # Initialize project first to ensure storage is ready
        init_result = runner.invoke(app, ["project", "init"])
        assert init_result.exit_code == 0

        result = runner.invoke(
            app,
            ["task", "create", "Test Task 2", "Details"],
        )

    assert result.exit_code == 0
    assert "Hook: task_created fired" not in result.stdout


def test_update_hook_output() -> None:
    """Test hook output for update command."""
    # Create a task first
    dispatcher = get_dispatcher()
    dispatcher.reset()

    with (
        runner.isolated_filesystem(),
        patch(
            "tasky_cli.commands.tasks.load_user_hooks",
        ),
    ):
        # Initialize project first to ensure storage is ready
        init_result = runner.invoke(app, ["project", "init"])
        assert init_result.exit_code == 0

        create_result = runner.invoke(
            app,
            ["task", "create", "Task to Update", "Details"],
        )
        assert create_result.exit_code == 0

        # Extract ID
        match = re.search(r"id: ([a-f0-9-]+)", create_result.stdout)
        if not match:
            # Try another format or fail
            match = re.search(r"([a-f0-9-]{36})", create_result.stdout)

        assert match, "Could not find task ID in output"
        task_id = match.group(1)

        # Update task
        result = runner.invoke(
            app,
            ["task", "--verbose-hooks", "update", task_id, "--name", "Updated Name"],
        )

        assert result.exit_code == 0
        assert "Hook: task_updated fired" in result.stdout
        assert (
            "Updated fields: ['name', 'updated_at']" in result.stdout
            or "Updated fields: ['updated_at', 'name']" in result.stdout
        )
