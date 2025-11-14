"""SQLite database schema definition for task storage."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3


# Schema version for migrations
SCHEMA_VERSION = 1

# SQL statement to create the tasks table
CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

# Index definitions for efficient querying
CREATE_INDEXES = [
    # Index for status filtering (most common query)
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    # Index for date-range filtering (future feature)
    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
    # Composite index for common queries (status + created_at ordering)
    "CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC)",
]


def create_schema(conn: sqlite3.Connection) -> None:
    """Create database schema with tables and indexes.

    Parameters
    ----------
    conn:
        Active SQLite connection

    """
    cursor = conn.cursor()

    # Create tasks table
    cursor.execute(CREATE_TASKS_TABLE)

    # Create indexes
    for index_sql in CREATE_INDEXES:
        cursor.execute(index_sql)

    # Set schema version
    cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    conn.commit()


def validate_schema(conn: sqlite3.Connection) -> bool:
    """Validate database integrity.

    Parameters
    ----------
    conn:
        Active SQLite connection

    Returns
    -------
    bool:
        True if schema is valid, False otherwise

    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()
    return result[0] == "ok" if result else False
