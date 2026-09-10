from __future__ import annotations

import sqlite3
from typing import List, Optional

DB_PATH = "database/ktu.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_chat_tables() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                subject_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                message_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


def get_subject_id(subject_name: str, department: Optional[str] = None) -> Optional[int]:
    conn = get_connection()
    try:
        query = """
            SELECT id
            FROM subjects
            WHERE LOWER(TRIM(subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " LIMIT 1"

        row = conn.execute(query, params).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def create_chat_session(user_id: str, subject_name: Optional[str] = None, department: Optional[str] = None) -> int:
    ensure_chat_tables()
    conn = get_connection()
    try:
        subject_id = get_subject_id(subject_name, department=department) if subject_name else None

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO chat_sessions (user_id, subject_id)
            VALUES (?, ?)
            """,
            (user_id, subject_id),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def add_message(session_id: int, role: str, message_text: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, message_text)
            VALUES (?, ?, ?)
            """,
            (session_id, role, message_text),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(session_id: int, limit: int = 10) -> List[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, message_text
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()

        # reverse so oldest comes first
        rows = list(rows)[::-1]

        return [
            {"role": row["role"], "content": row["message_text"]}
            for row in rows
        ]
    finally:
        conn.close()


def get_latest_session(user_id: str, subject_id: Optional[int] = None) -> Optional[int]:
    conn = get_connection()
    try:
        query = "SELECT id FROM chat_sessions WHERE user_id = ?"
        params: list = [user_id]
        if subject_id is not None:
            query += " AND subject_id = ?"
            params.append(subject_id)
        else:
            query += " AND subject_id IS NULL"
        query += " ORDER BY id DESC LIMIT 1"

        row = conn.execute(query, params).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def get_or_create_session(user_id: str, subject_name: Optional[str] = None, department: Optional[str] = None) -> int:
    """Resumes the latest session for this exact (user, subject) pair rather than
    the user's overall latest session, so switching subjects doesn't leak in another
    subject's chat history."""
    subject_id = get_subject_id(subject_name, department=department) if subject_name else None

    session_id = get_latest_session(user_id, subject_id=subject_id)
    if session_id is not None:
        return session_id
    return create_chat_session(user_id, subject_name, department=department)


if __name__ == "__main__":
    user_id = "demo_user"
    subject_name = "Operating Systems"

    session_id = create_chat_session(user_id, subject_name)
    print(f"Created session: {session_id}")

    add_message(session_id, "user", "Explain deadlock prevention.")
    add_message(session_id, "assistant", "Deadlock prevention ensures that at least one necessary condition for deadlock never holds.")

    history = get_chat_history(session_id)
    print("\nChat History:")
    for msg in history:
        print(msg)