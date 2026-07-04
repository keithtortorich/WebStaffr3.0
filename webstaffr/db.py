"""Connection handling and schema migrations for the SQLite persistence layer.

Kept deliberately minimal: stdlib `sqlite3` only, no ORM, no new dependency.
Migrations are plain numbered .sql files under `webstaffr/migrations/`,
applied once each and tracked in a `schema_migrations` table -- enough
structure to evolve the schema safely without pulling in a migration
framework for two tables.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
from pathlib import Path
from typing import Iterator

logger = logging.getLogger("webstaffr.db")

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class StorageError(RuntimeError):
    """Raised for any persistence-layer failure. Callers get one clear,
    documented exception type instead of leaking raw sqlite3 errors."""


@contextlib.contextmanager
def connect(db_path: str) -> Iterator[sqlite3.Connection]:
    """Open a connection with sane defaults, commit on success, roll back
    and re-raise (wrapped) on failure, always close.

    `db_path` may be a filesystem path or ":memory:" for tests.
    """
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as exc:
        raise StorageError(f"Could not open database at {db_path!r}: {exc}") from exc

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate(conn: sqlite3.Connection) -> list[str]:
    """Apply any migration under webstaffr/migrations/ not yet recorded as
    applied. Returns the list of migration filenames applied this call
    (empty if the schema was already current). Idempotent -- safe to call
    on every startup.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()

    applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}

    if not _MIGRATIONS_DIR.is_dir():
        raise StorageError(f"Migrations directory not found: {_MIGRATIONS_DIR}")

    migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise StorageError(f"No migration files found in {_MIGRATIONS_DIR}")

    newly_applied = []
    for path in migration_files:
        version = path.stem  # e.g. "0001_initial"
        if version in applied:
            continue
        sql = path.read_text()
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
            )
            conn.commit()
            newly_applied.append(version)
            logger.info("migration_applied version=%s", version)
        except sqlite3.Error as exc:
            conn.rollback()
            raise StorageError(f"Migration {version!r} failed: {exc}") from exc

    return newly_applied
