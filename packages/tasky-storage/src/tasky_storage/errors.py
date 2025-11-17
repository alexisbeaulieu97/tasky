"""Exceptions for Tasky storage module.

This module defines a custom exception hierarchy for all storage operations,
ensuring consistent error handling across all backends and preventing raw
built-in exceptions from leaking to callers.

Exception Hierarchy:
    StorageError (base)
      ├── StorageConfigurationError (invalid configuration)
      ├── SnapshotConversionError (invalid snapshot dict → TaskModel conversion)
      ├── StorageDataError (Pydantic validation, field validation failures)
      ├── TransactionConflictError (concurrent write conflicts detected)
      └── StorageIOError (wraps OS/I/O errors: OSError, FileNotFoundError, etc.)

Error Behavior Mapping:
    - SnapshotConversionError → Log: ERROR → Action: Do not retry
    - StorageDataError → Log: WARNING → HTTP: 400 Bad Request → Action: Do not retry
    - TransactionConflictError → Log: WARNING → Action: Retry once, then fail
    - StorageIOError → Log: ERROR → HTTP: 500 Internal Server Error → Action: Retry once
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError

if TYPE_CHECKING:
    from pydantic import ValidationError


class StorageError(Exception):
    """Base exception for storage-related errors.

    All storage operations should raise exceptions that inherit from this base class.
    This allows callers to catch all storage-related errors with a single except clause.
    """


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid.

    Examples:
        - Invalid backend type specified
        - Missing required configuration parameters
        - Contradictory configuration options

    """


class SnapshotConversionError(StorageError):
    """Raised when snapshot dict → TaskModel conversion fails.

    This error indicates corrupted or invalid data in storage that cannot be
    parsed into a valid TaskModel. Unlike validation errors during task creation,
    this represents data corruption in the persistence layer.

    Attributes:
        message: Actionable error message describing what went wrong
        cause: Original exception that triggered the conversion failure

    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize SnapshotConversionError.

        Parameters
        ----------
        message:
            Actionable error message
            (e.g., "Failed to convert snapshot: missing required field 'id'")
        cause:
            Original exception that triggered the error, preserved for debugging

        """
        super().__init__(message)
        if cause:
            self.__cause__ = cause


class StorageDataError(StorageError):
    """Raised when stored data fails Pydantic validation or field validation.

    This error is raised when data validation fails, such as:
    - Invalid UUID format
    - Invalid enum values
    - Type mismatches
    - Constraint violations

    This class implements the StorageErrorProtocol from tasky-tasks, allowing
    the domain layer to catch storage errors without directly importing this class.

    Attributes:
        message: Error message with validation details
        cause: Original ValidationError for debugging

    """

    __is_storage_error__ = True  # Marker for StorageErrorProtocol

    def __init__(self, exc: ValidationError | str, cause: Exception | None = None) -> None:
        """Initialize StorageDataError.

        Parameters
        ----------
        exc:
            Either a Pydantic ValidationError or a custom error message string
        cause:
            Optional original exception for additional context

        """
        if isinstance(exc, PydanticValidationError):
            msg = f"Stored task data is invalid: {exc}"
            super().__init__(msg)
            # Preserve ValidationError as __cause__ for debugging
            self.__cause__ = exc
        else:
            super().__init__(exc)
            if cause:
                self.__cause__ = cause


class TransactionConflictError(StorageError):
    """Raised when concurrent write conflicts are detected.

    This error indicates that a transaction failed due to concurrent modification
    by another process or thread. Examples:
    - JSON file timestamp mismatch (optimistic locking failure)
    - SQLite BUSY or LOCKED error
    - Database serialization failure

    This error should trigger a retry strategy (typically retry once, then fail).

    Attributes:
        message: Description of the conflict
        cause: Original database/filesystem error

    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize TransactionConflictError.

        Parameters
        ----------
        message:
            Description of the conflict
        cause:
            Original exception that triggered the conflict detection

        """
        super().__init__(message)
        if cause:
            self.__cause__ = cause


class StorageIOError(StorageError):
    """Raised when I/O operations fail.

    Wraps OS-level and filesystem errors to provide consistent error handling:
    - File not found
    - Permission denied
    - Disk full
    - Database locked/inaccessible
    - Network storage unavailable

    This error should trigger a retry strategy for transient failures.

    Attributes:
        message: Actionable error message
        cause: Original OS/filesystem exception

    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize StorageIOError.

        Parameters
        ----------
        message:
            Actionable error message describing the I/O failure
        cause:
            Original OSError, IOError, or database exception

        """
        super().__init__(message)
        if cause:
            self.__cause__ = cause
