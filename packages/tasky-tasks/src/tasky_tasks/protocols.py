"""Protocol definitions for decoupling domain from infrastructure concerns."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageErrorProtocol(Protocol):
    """Protocol for storage-layer data validation errors.

    This protocol allows the domain layer (tasky-tasks) to catch storage errors
    without directly depending on the infrastructure package (tasky-storage).

    Any exception implementing this protocol indicates that data retrieved from
    or written to storage failed validation checks (e.g., Pydantic validation,
    field validation, or data type mismatches).

    Implementation Note
    -------------------
    Classes implementing this protocol MUST inherit from Exception and include
    a specific marker attribute to distinguish them from generic exceptions.

    Usage
    -----
    In service methods, catch Exception and check if it matches this protocol:

        try:
            task = repository.get_task(task_id)
        except Exception as exc:
            if isinstance(exc, StorageErrorProtocol):
                raise TaskValidationError(...) from exc
            raise

    """

    __is_storage_error__: bool
    """Marker attribute to identify storage errors (must be True)."""

    @property
    def args(self) -> tuple[object, ...]:
        """Exception arguments for string representation."""
        ...

    def __str__(self) -> str:
        """Human-readable error message."""
        ...
