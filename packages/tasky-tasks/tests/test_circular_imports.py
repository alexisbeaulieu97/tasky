"""Tests to verify no circular imports in tasky-tasks package."""

from __future__ import annotations


def test_models_can_import_independently() -> None:
    """Verify TaskModel can be imported without side effects."""
    from tasky_tasks.models import TaskModel  # noqa: PLC0415

    assert TaskModel is not None


def test_exceptions_can_import_independently() -> None:
    """Verify exceptions can be imported without side effects."""
    from tasky_tasks.exceptions import InvalidStateTransitionError  # noqa: PLC0415

    assert InvalidStateTransitionError is not None


def test_enums_can_import_independently() -> None:
    """Verify TaskStatus can be imported without side effects."""
    from tasky_tasks.enums import TaskStatus  # noqa: PLC0415

    assert TaskStatus is not None


def test_import_order_does_not_matter_models_first() -> None:
    """Verify importing models first doesn't cause circular import."""
    # This would fail if there was a circular dependency
    from tasky_tasks import TaskModel  # noqa: PLC0415
    from tasky_tasks.exceptions import InvalidStateTransitionError  # noqa: PLC0415

    task = TaskModel(name="Test", details="Details")
    assert task is not None
    assert InvalidStateTransitionError is not None


def test_import_order_does_not_matter_exceptions_first() -> None:
    """Verify importing exceptions first doesn't cause circular import."""
    # This would fail if there was a circular dependency
    from tasky_tasks.exceptions import InvalidStateTransitionError  # noqa: PLC0415
    from tasky_tasks import TaskModel  # noqa: PLC0415

    assert InvalidStateTransitionError is not None
    task = TaskModel(name="Test", details="Details")
    assert task is not None
