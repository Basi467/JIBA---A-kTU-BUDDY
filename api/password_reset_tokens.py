from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from db_path import get_db_path

RESET_TOKEN_TTL_MINUTES = 30


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def issue_reset_token(user_id: int) -> str:
    """Mints a single-use, short-lived token for the password_resets table
    (migration 0002). Unlike auth_sessions' 30-day login tokens, this one
    expires in 30 minutes and is marked used_at the moment it's redeemed,
    so a leaked reset link can't be replayed."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)).isoformat()

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at),
        )
        conn.commit()
    finally:
        conn.close()

    return token


def resolve_reset_token(token: str) -> Optional[int]:
    """Returns the user_id for a valid, unexpired, unused token — or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at, used_at FROM password_resets WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()

    if not row or row["used_at"] is not None:
        return None

    expires_at = row["expires_at"]
    if "+" not in expires_at and "Z" not in expires_at:
        # Stored via isoformat() on a tz-aware datetime, so this branch is
        # defensive only — kept simple rather than pulling in a tz library.
        expires_at += "+00:00"

    if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        return None

    return row["user_id"]


def mark_used(token: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE password_resets SET used_at = ? WHERE token = ?",
            (datetime.now(timezone.utc).isoformat(), token),
        )
        conn.commit()
    finally:
        conn.close()
