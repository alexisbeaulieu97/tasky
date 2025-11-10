class StorageError(Exception):
    """Base exception for storage-related errors."""

    pass


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid."""

    pass


class StorageDataError(StorageError):
    """Raised when data cannot be serialized/deserialized."""

    pass
