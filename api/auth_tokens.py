from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "database" / "ktu.db"

SESSION_TTL_DAYS = 30


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def issue_token(user_id: int) -> str:
    """Mints an opaque bearer token for the API, backed by the same
    auth_sessions table the Streamlit app's session_store.py uses (there via
    a URL query param, here via an Authorization header) — one shared,
    per-login session table for both frontends."""
    ensure_table()

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)).isoformat()

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO auth_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
        conn.commit()
    finally:
        conn.close()

    return token


def resolve_token(token: str) -> Optional[int]:
    ensure_table()

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at FROM auth_sessions WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return None

    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        revoke_token(token)
        return None

    return row["user_id"]


def revoke_token(token: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
