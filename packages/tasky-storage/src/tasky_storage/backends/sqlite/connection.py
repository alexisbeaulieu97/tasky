"""SQLite connection management with pooling and thread-safety."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from tasky_logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

logger = get_logger("storage.sqlite.connection")


class ConnectionManager:
    """Manages SQLite connections with thread-safe pooling.

    Uses a single connection per database file with RLock for thread-safety.
    SQLite's WAL mode handles concurrent readers efficiently.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: dict[str, sqlite3.Connection] = {}
        self._locks: dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()

    def get_connection(self, path: Path) -> Generator[sqlite3.Connection]:
        """Get a thread-safe connection to the database.

        Parameters
        ----------
        path:
            Path to the SQLite database file

        Yields
        ------
        sqlite3.Connection:
            Database connection with Row factory enabled

        """
        path_str = str(path.resolve())

        # Ensure connection and lock exist
        with self._global_lock:
            if path_str not in self._connections:
                logger.debug("Creating new connection: path=%s", path_str)
                conn = self._create_connection(path)
                self._connections[path_str] = conn
                self._locks[path_str] = threading.RLock()

        # Acquire lock and yield connection
        lock = self._locks[path_str]
        with lock:
            conn = self._connections[path_str]
            yield conn

    def _create_connection(self, path: Path) -> sqlite3.Connection:
        """Create and configure a new SQLite connection.

        Parameters
        ----------
        path:
            Path to the SQLite database file

        Returns
        -------
        sqlite3.Connection:
            Configured connection with WAL mode and Row factory

        """
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # Configure WAL mode for better concurrency
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")  # 5 seconds
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.commit()

        return conn

    def close_all(self) -> None:
        """Close all connections."""
        with self._global_lock:
            for path_str, conn in self._connections.items():
                logger.debug("Closing connection: path=%s", path_str)
                conn.close()
            self._connections.clear()
            self._locks.clear()


# Global connection manager instance
_connection_manager = ConnectionManager()


@contextmanager
def get_connection(path: Path) -> Generator[sqlite3.Connection]:
    """Get a thread-safe connection to a SQLite database.

    Parameters
    ----------
    path:
        Path to the SQLite database file

    Yields
    ------
    sqlite3.Connection:
        Database connection

    """
    yield from _connection_manager.get_connection(path)
