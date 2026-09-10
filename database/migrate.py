from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Set

from db import get_db_path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _migration_files() -> List[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda p: p.name)


def _version_of(path: Path) -> int:
    return int(path.name.split("_", 1)[0])


def _applied_versions(conn: sqlite3.Connection) -> Set[int]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()

    # Backfill: a database created before this migration system existed
    # already has the baseline schema (via the old init__db.py) but no
    # tracking row for it. Detect that case via a table the baseline creates
    # and mark version 1 applied retroactively instead of re-running it
    # (which would fail on the non-idempotent `CREATE TABLE subjects ...`).
    if 1 not in _applied_versions(conn):
        baseline_already_applied = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'"
        ).fetchone()
        if baseline_already_applied:
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (1, '0001_baseline')"
            )
            conn.commit()


def migrate(db_path: Optional[Path] = None) -> List[int]:
    """Applies every migration in database/migrations/ that hasn't run yet,
    in version order. Returns the list of newly-applied version numbers
    (empty if the database was already up to date)."""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    try:
        _ensure_migrations_table(conn)
        already = _applied_versions(conn)

        newly_applied = []
        for migration_file in _migration_files():
            version = _version_of(migration_file)
            if version in already:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (version, migration_file.stem),
            )
            conn.commit()
            newly_applied.append(version)

        return newly_applied
    finally:
        conn.close()


if __name__ == "__main__":
    applied = migrate()
    if applied:
        print(f"Applied migrations: {applied}")
    else:
        print("Database already up to date.")
