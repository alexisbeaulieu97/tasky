import pytest

from tasky_core.hooks import HookExecutionError, TaskPreAddPayload, TaskPreImportPayload


def test_task_pre_add_payload_validation() -> None:
    with pytest.raises(HookExecutionError):
        TaskPreAddPayload.from_mapping({"details": "body"})


def test_task_pre_import_payload_requires_task_list() -> None:
    with pytest.raises(HookExecutionError):
        TaskPreImportPayload.from_mapping({"strategy": "append", "tasks": "oops"})
