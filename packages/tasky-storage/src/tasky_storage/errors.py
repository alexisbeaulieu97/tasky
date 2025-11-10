class StorageError(Exception):
    """Base exception for storage-related failures."""


class StorageDataError(StorageError):
    """Raised when persisted data is malformed or cannot be parsed."""
