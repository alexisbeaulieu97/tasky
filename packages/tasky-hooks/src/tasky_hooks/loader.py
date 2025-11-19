"""Loader for user-defined hooks."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

logger = logging.getLogger("tasky.hooks.loader")


def load_user_hooks() -> None:
    """Load user hooks from ~/.tasky/hooks.py.

    This function attempts to import the user's hooks file. The file is expected
    to contain code that registers handlers with the global dispatcher.
    """
    hooks_path = Path.home() / ".tasky" / "hooks.py"
    if not hooks_path.exists():
        logger.debug("No user hooks file found at %s", hooks_path)
        return

    logger.debug("Loading user hooks from %s", hooks_path)

    try:
        spec = importlib.util.spec_from_file_location("user_hooks", hooks_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["user_hooks"] = module
            spec.loader.exec_module(module)
            logger.info("User hooks loaded successfully")
    except Exception:
        logger.exception("Failed to load user hooks from %s", hooks_path)
