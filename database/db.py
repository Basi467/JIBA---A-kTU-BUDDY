import os
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    """Single source of truth for the sqlite file location, for scripts run
    from inside database/. src/ has its own copy (db_path.py) since this
    directory isn't on its sys.path — kept in sync manually. KTU_DB_PATH lets
    tests and Docker point at a different file without touching any code."""
    override = os.environ.get("KTU_DB_PATH")
    if override:
        return Path(override)
    return ROOT_DIR / "database" / "ktu.db"


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn
