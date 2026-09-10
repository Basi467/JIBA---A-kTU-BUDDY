from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from typing import Optional

DB_PATH = "database/ktu.db"

PBKDF2_ITERATIONS = 260_000


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """PBKDF2-HMAC-SHA256 with a high iteration count. Deliberately slow,
    unlike a bare SHA-256 hash, to resist offline brute-force cracking."""
    if salt is None:
        salt = os.urandom(16).hex()
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        if stored_hash.startswith("pbkdf2$"):
            _, iterations_str, salt, hashed = stored_hash.split("$", 3)
            derived = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations_str)
            )
            return hmac.compare_digest(derived.hex(), hashed)

        # Legacy salt$sha256 format from before the PBKDF2 upgrade — kept so
        # accounts created before this change can still log in.
        salt, hashed = stored_hash.split("$", 1)
        check = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(check, hashed)
    except Exception:
        return False


def register_user(
    name: str,
    email: str,
    password: str,
    scheme: str,
    department: str,
    semester: int,
) -> int:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE LOWER(email) = LOWER(?)",
            (email.strip(),),
        ).fetchone()

        if existing:
            raise ValueError("User with this email already exists.")

        password_hash = hash_password(password)

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, scheme, department, semester)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                password_hash,
                scheme.strip(),
                department.strip(),
                int(semester),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def login_user(email: str, password: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    try:
        user = conn.execute(
            """
            SELECT id, name, email, password_hash, scheme, department, semester
            FROM users
            WHERE LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (email.strip(),),
        ).fetchone()

        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return user
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    try:
        user = conn.execute(
            """
            SELECT id, name, email, scheme, department, semester, created_at
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return user
    finally:
        conn.close()


# A subject counts as "complete" when it has the standard 5-module KTU
# structure AND has past-year questions linked to real topics — i.e. every
# Exam Mode feature (predicted topics, teach queue, repeated questions) has
# real data to show, not an empty state. Subjects that don't meet this bar
# are hidden from students entirely rather than shown half-populated.
COMPLETE_SUBJECT_FILTER = """
    (SELECT COUNT(*) FROM modules m WHERE m.subject_id = s.id) = 5
    AND EXISTS (
        SELECT 1 FROM pyq_questions q
        WHERE q.subject_id = s.id AND q.topic_id IS NOT NULL
    )
"""


def get_subjects_for_user(user_id: int):
    conn = get_connection()
    try:
        user = conn.execute(
            """
            SELECT scheme, department, semester
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if not user:
            return []

        rows = conn.execute(
            f"""
            SELECT subject_code, subject_name
            FROM subjects s
            WHERE scheme = ?
              AND department = ?
              AND semester = ?
              AND {COMPLETE_SUBJECT_FILTER}
            ORDER BY subject_name
            """,
            (
                user["scheme"],
                user["department"],
                user["semester"],
            ),
        ).fetchall()

        return rows
    finally:
        conn.close()


if __name__ == "__main__":
    # Demo
    try:
        user_id = register_user(
            name="Demo User",
            email="demo111223@example.com",
            password="demo123",
            scheme="KTU_2019",
            department="COMMON",
            semester=7,
        )
        print("Registered user id:", user_id)
    except ValueError as e:
        print("Register:", e)

    user = login_user("demo111223@example.com", "demo123")
    if user:
        print("Login success:", dict(user))
        subjects = get_subjects_for_user(user["id"])
        print("Subjects:")
        for s in subjects[:10]:
            print(dict(s))
    else:
        print("Login failed")