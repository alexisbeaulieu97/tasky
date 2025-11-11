"""Exceptions for Tasky storage module."""

from pydantic import ValidationError


class StorageError(Exception):
    """Base exception for storage-related errors."""


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid."""


class StorageDataError(StorageError):
    """Raised when stored data is invalid."""

    def __init__(self, exc: ValidationError | str) -> None:
        """Initialize StorageDataError with a ValidationError or message string."""
        msg = f"Stored task data is invalid: {exc}" if isinstance(exc, ValidationError) else exc
        super().__init__(msg)
