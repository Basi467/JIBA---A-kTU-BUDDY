from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from db_path import get_db_path

DB_PATH = get_db_path()


@dataclass
class ModuleTopicPriority:
    subject_name: str
    module_no: int
    topic_name: str
    question_count: int
    weighted_score: float
    priority_label: str


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS module_topic_priority (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            module_no INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            question_count INTEGER NOT NULL DEFAULT 0,
            weighted_score REAL NOT NULL DEFAULT 0,
            priority_label TEXT NOT NULL CHECK (priority_label IN ('High', 'Medium', 'Low')),
            UNIQUE(subject_id, module_no, topic_id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()


def classify_within_module(rows: list[sqlite3.Row]) -> list[tuple[int, str]]:
    """
    Rank topics inside one module only.
    Top 30% -> High
    Next 40% -> Medium
    Rest -> Low
    """
    if not rows:
        return []

    sorted_rows = sorted(
        rows,
        key=lambda r: (float(r["weighted_score"]), int(r["question_count"])),
        reverse=True,
    )

    n = len(sorted_rows)
    high_cut = max(1, round(n * 0.30))
    med_cut = max(high_cut + 1, round(n * 0.70)) if n > 1 else 1

    result: list[tuple[int, str]] = []
    for idx, row in enumerate(sorted_rows):
        if idx < high_cut:
            label = "High"
        elif idx < med_cut:
            label = "Medium"
        else:
            label = "Low"
        result.append((row["topic_id"], label))
    return result


def rebuild_module_topic_priority() -> None:
    conn = get_connection()
    try:
        ensure_table(conn)
        conn.execute("DELETE FROM module_topic_priority")

        grouped = conn.execute(
            """
            SELECT
                s.id AS subject_id,
                s.subject_name,
                q.module_no,
                t.id AS topic_id,
                t.topic_name,
                COUNT(q.id) AS question_count,
                SUM(
                    CASE
                        WHEN q.marks >= 8 THEN 1.5
                        ELSE 1.0
                    END
                ) AS weighted_score
            FROM pyq_questions q
            JOIN subjects s ON q.subject_id = s.id
            JOIN topics t ON q.topic_id = t.id
            WHERE q.topic_id IS NOT NULL
              AND q.module_no IS NOT NULL
            GROUP BY s.id, s.subject_name, q.module_no, t.id, t.topic_name
            ORDER BY s.subject_name, q.module_no, weighted_score DESC, question_count DESC
            """
        ).fetchall()

        # bucket by subject + module
        module_buckets: dict[tuple[int, int], list[sqlite3.Row]] = {}
        for row in grouped:
            key = (int(row["subject_id"]), int(row["module_no"]))
            module_buckets.setdefault(key, []).append(row)

        inserted = 0

        for (subject_id, module_no), rows in module_buckets.items():
            labels = dict(classify_within_module(rows))

            for row in rows:
                conn.execute(
                    """
                    INSERT INTO module_topic_priority (
                        subject_id,
                        module_no,
                        topic_id,
                        question_count,
                        weighted_score,
                        priority_label
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subject_id,
                        module_no,
                        int(row["topic_id"]),
                        int(row["question_count"]),
                        float(row["weighted_score"] or 0),
                        labels[int(row["topic_id"])],
                    ),
                )
                inserted += 1

        conn.commit()
        print(f"module_topic_priority updated successfully. Rows inserted: {inserted}")
    finally:
        conn.close()


def preview_subject(subject_name: str, department: Optional[str] = None) -> list[ModuleTopicPriority]:
    conn = get_connection()
    try:
        query = """
            SELECT
                s.subject_name,
                mtp.module_no,
                t.topic_name,
                mtp.question_count,
                mtp.weighted_score,
                mtp.priority_label
            FROM module_topic_priority mtp
            JOIN subjects s ON mtp.subject_id = s.id
            JOIN topics t ON mtp.topic_id = t.id
            WHERE LOWER(TRIM(s.subject_name)) = LOWER(TRIM(?))
        """
        params: list = [subject_name]
        if department:
            query += " AND LOWER(TRIM(s.department)) = LOWER(TRIM(?))"
            params.append(department)
        query += " ORDER BY mtp.module_no, mtp.weighted_score DESC, mtp.question_count DESC, t.topic_name"

        rows = conn.execute(query, params).fetchall()

        return [
            ModuleTopicPriority(
                subject_name=row["subject_name"],
                module_no=int(row["module_no"]),
                topic_name=row["topic_name"],
                question_count=int(row["question_count"]),
                weighted_score=float(row["weighted_score"]),
                priority_label=row["priority_label"],
            )
            for row in rows
        ]
    finally:
        conn.close()


if __name__ == "__main__":
    rebuild_module_topic_priority()

    sample_subject = "Operating Systems"
    preview = preview_subject(sample_subject)

    current_module: Optional[int] = None
    print(f"\nPreview for: {sample_subject}\n")
    for item in preview[:25]:
        if item.module_no != current_module:
            current_module = item.module_no
            print(f"\nModule {current_module}")
        print(
            f"- {item.topic_name} | count={item.question_count} | "
            f"score={item.weighted_score:.2f} | {item.priority_label}"
        )