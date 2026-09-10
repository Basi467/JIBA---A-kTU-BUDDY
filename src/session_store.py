from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import streamlit as st

from db_path import get_db_path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = get_db_path()

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


def save_session(user_id: int) -> None:
    """Logs a user in by minting a per-browser token stored in the URL's
    query params and recorded in the DB, rather than a single shared file
    on disk. A flat session.json file would be overwritten by whichever
    user logged in last on a hosted deployment, silently hijacking every
    other concurrent user's session."""
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

    st.query_params["session"] = token


def load_session() -> Optional[int]:
    ensure_table()

    token = st.query_params.get("session")
    if not token:
        return None

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
        clear_session()
        return None

    return row["user_id"]


def clear_session() -> None:
    token = st.query_params.get("session")

    if token:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()

    if "session" in st.query_params:
        del st.query_params["session"]
