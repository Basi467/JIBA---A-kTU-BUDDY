from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    """Single source of truth for the sqlite file location, for every module
    that has src/ on its sys.path (api/, app/, and src/ itself). database/
    scripts keep their own copy (db.py) since that directory isn't on this
    path — kept in sync manually. KTU_DB_PATH lets tests and Docker point at
    a different file without touching any code."""
    override = os.environ.get("KTU_DB_PATH")
    if override:
        return Path(override)
    return ROOT_DIR / "database" / "ktu.db"
