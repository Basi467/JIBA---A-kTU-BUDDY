from __future__ import annotations

import sqlite3
from typing import Optional, List, Dict

from db_path import get_db_path

DB_PATH = get_db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('not_started', 'in_progress', 'completed', 'weak')
                ),
                last_updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, topic_id),
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS topic_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_value TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


def get_topic_id(subject_name: str, topic_name: str, department: Optional[str] = None) -> Optional[int]:
    conn = get_connection()
    try:
        query = """
            SELECT t.id
            FROM topics t
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
              AND LOWER(TRIM(t.topic_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name, topic_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " LIMIT 1"

        row = conn.execute(query, params).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def get_topic_info(topic_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                t.id AS topic_id,
                t.topic_name,
                m.module_no,
                m.module_title,
                s.subject_name
            FROM topics t
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE t.id = ?
            LIMIT 1
            """,
            (topic_id,),
        ).fetchone()
        return row
    finally:
        conn.close()


def log_topic_activity(
    user_id: str,
    subject_name: str,
    topic_name: str,
    activity_type: str,
    activity_value: Optional[str] = None,
    department: Optional[str] = None,
) -> None:
    """
    activity_type can be:
    - viewed
    - asked_question
    - studied
    - solved_pyq
    - marked_weak
    - marked_completed
    - marked_in_progress
    """
    ensure_tables()

    topic_id = get_topic_id(subject_name, topic_name, department=department)
    if topic_id is None:
        raise ValueError(f"Topic not found: {topic_name} in subject: {subject_name}")

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO topic_activity (user_id, topic_id, activity_type, activity_value)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, topic_id, activity_type, activity_value),
        )
        conn.commit()
    finally:
        conn.close()

    recompute_topic_status(user_id, topic_id)


def get_activity_counts(user_id: str, topic_id: int) -> Dict[str, int]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT activity_type, COUNT(*) AS cnt
            FROM topic_activity
            WHERE user_id = ? AND topic_id = ?
            GROUP BY activity_type
            """,
            (user_id, topic_id),
        ).fetchall()

        counts = {
            "viewed": 0,
            "asked_question": 0,
            "studied": 0,
            "solved_pyq": 0,
            "marked_weak": 0,
            "marked_completed": 0,
            "marked_in_progress": 0,
        }

        for row in rows:
            counts[row["activity_type"]] = row["cnt"]

        return counts
    finally:
        conn.close()


def infer_status_from_activity(counts: Dict[str, int]) -> str:
    """
    Rule priority:
    1. explicit weak mark -> weak
    2. explicit completed mark -> completed
    3. studied + solved_pyq >= threshold -> completed
    4. asked_question >= threshold -> weak
    5. viewed/studied/marked_in_progress -> in_progress
    6. else -> not_started
    """
    if counts["marked_completed"] > 0:
        return "completed"

    if counts["marked_weak"] > 0:
        return "weak"

    if counts["studied"] >= 1 and counts["solved_pyq"] >= 2:
        return "completed"

    if counts["asked_question"] >= 3:
        return "weak"

    if counts["marked_in_progress"] > 0:
        return "in_progress"

    if counts["viewed"] >= 1 or counts["studied"] >= 1 or counts["solved_pyq"] >= 1:
        return "in_progress"

    return "not_started"


def upsert_progress(user_id: str, topic_id: int, status: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO user_progress (user_id, topic_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, topic_id) DO UPDATE SET
                status = excluded.status,
                last_updated = CURRENT_TIMESTAMP
            """,
            (user_id, topic_id, status),
        )
        conn.commit()
    finally:
        conn.close()


def recompute_topic_status(user_id: str, topic_id: int) -> str:
    ensure_tables()
    counts = get_activity_counts(user_id, topic_id)
    status = infer_status_from_activity(counts)
    upsert_progress(user_id, topic_id, status)
    return status


def auto_update_progress(
    user_id: str,
    subject_name: str,
    topic_name: str,
    interaction_type: str,
    interaction_value: Optional[str] = None,
    department: Optional[str] = None,
) -> str:
    """
    Convenience wrapper for UI or backend integrations.
    Logs activity and returns the latest inferred status.
    """
    log_topic_activity(
        user_id=user_id,
        subject_name=subject_name,
        topic_name=topic_name,
        activity_type=interaction_type,
        activity_value=interaction_value,
        department=department,
    )

    topic_id = get_topic_id(subject_name, topic_name, department=department)
    if topic_id is None:
        raise ValueError(f"Topic not found after logging activity: {topic_name}")

    return get_topic_status(user_id, topic_id)


def get_topic_status(user_id: str, topic_id: int) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT status
            FROM user_progress
            WHERE user_id = ? AND topic_id = ?
            LIMIT 1
            """,
            (user_id, topic_id),
        ).fetchone()
        return row["status"] if row else "not_started"
    finally:
        conn.close()


def get_user_progress(user_id: str, subject_name: str, department: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        query = """
            SELECT
                t.topic_name,
                m.module_no,
                up.status,
                up.last_updated
            FROM user_progress up
            JOIN topics t ON up.topic_id = t.id
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE up.user_id = ?
              AND LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [user_id, subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " ORDER BY m.module_no, t.topic_name"

        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def get_topic_activity_history(
    user_id: str, subject_name: str, topic_name: str, department: Optional[str] = None
) -> List[sqlite3.Row]:
    topic_id = get_topic_id(subject_name, topic_name, department=department)
    if topic_id is None:
        return []

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT activity_type, activity_value, created_at
            FROM topic_activity
            WHERE user_id = ? AND topic_id = ?
            ORDER BY id DESC
            """,
            (user_id, topic_id),
        ).fetchall()
        return rows
    finally:
        conn.close()


def _get_topics_by_status(user_id: str, subject_name: str, status: str, department: Optional[str] = None) -> List[str]:
    conn = get_connection()
    try:
        query = """
            SELECT t.topic_name
            FROM user_progress up
            JOIN topics t ON up.topic_id = t.id
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE up.user_id = ?
              AND up.status = ?
              AND LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [user_id, status, subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " ORDER BY m.module_no, t.topic_name"

        rows = conn.execute(query, params).fetchall()
        return [row["topic_name"] for row in rows]
    finally:
        conn.close()


def get_weak_topics(user_id: str, subject_name: str, department: Optional[str] = None) -> List[str]:
    return _get_topics_by_status(user_id, subject_name, "weak", department=department)


def get_completed_topics(user_id: str, subject_name: str, department: Optional[str] = None) -> List[str]:
    return _get_topics_by_status(user_id, subject_name, "completed", department=department)


def get_in_progress_topics(user_id: str, subject_name: str, department: Optional[str] = None) -> List[str]:
    return _get_topics_by_status(user_id, subject_name, "in_progress", department=department)


if __name__ == "__main__":
    ensure_tables()

    user_id = "demo_user"
    subject_name = "Operating Systems"
    topic_name = "Deadlock prevention"

    # simulate actions
    log_topic_activity(user_id, subject_name, topic_name, "viewed")
    log_topic_activity(user_id, subject_name, topic_name, "asked_question")
    log_topic_activity(user_id, subject_name, topic_name, "asked_question")
    log_topic_activity(user_id, subject_name, topic_name, "asked_question")

    topic_id = get_topic_id(subject_name, topic_name)
    if topic_id is not None:
        status = get_topic_status(user_id, topic_id)
        print(f"Current status for '{topic_name}': {status}")

    print("\nWeak topics:")
    print(get_weak_topics(user_id, subject_name))

    print("\nFull progress:")
    for row in get_user_progress(user_id, subject_name):
        print(dict(row))