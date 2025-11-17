from __future__ import annotations

import json

import pytest

from tasky_hooks.errors import (
    ErrorResult,
    format_error_for_cli,
    log_fields_for_error,
    serialize_error_for_mcp,
)


def test_error_result_validation() -> None:
    result = ErrorResult(message="Boom", suggestion=None, exit_code=2, traceback=None)
    assert result.message == "Boom"


def test_error_result_rejects_bad_exit_code() -> None:
    with pytest.raises(ValueError):
        ErrorResult(message="bad", suggestion=None, exit_code=0, traceback=None)


def test_cli_formatter_includes_traceback() -> None:
    result = ErrorResult(
        message="Missing task",
        suggestion="Run 'tasky task list'.",
        exit_code=1,
        traceback="Traceback...",
    )

    rendered = format_error_for_cli(result)

    assert "Error: Missing task" in rendered
    assert "Suggestion: Run 'tasky task list'." in rendered
    assert "Traceback..." in rendered


def test_mcp_serializer_and_log_fields() -> None:
    result = ErrorResult(
        message="Storage failure",
        suggestion="Check .tasky directory.",
        exit_code=3,
        traceback=None,
    )

    payload = json.loads(serialize_error_for_mcp(result))
    assert payload == {
        "error": "Storage failure",
        "hint": "Check .tasky directory.",
        "code": 3,
    }

    log_payload = log_fields_for_error(result)
    assert log_payload["exit_code"] == 3
    assert log_payload["message"] == "Storage failure"
