from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

DB_PATH = "database/ktu.db"


@dataclass
class ProbabilityConfig:
    recent_year: int = 2026
    freq_weight: float = 0.7
    recency_weight: float = 0.3


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_probability_columns(conn: sqlite3.Connection) -> None:
    cols = conn.execute("PRAGMA table_info(topic_importance)").fetchall()
    existing = {row["name"] for row in cols}

    if "probability_score" not in existing:
        conn.execute("ALTER TABLE topic_importance ADD COLUMN probability_score REAL DEFAULT 0")
    if "probability_label" not in existing:
        conn.execute("ALTER TABLE topic_importance ADD COLUMN probability_label TEXT DEFAULT 'Low'")

    conn.commit()


def classify_probability(score: float) -> str:
    if score >= 75:
        return "Very High"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"


def build_probability_engine(cfg: Optional[ProbabilityConfig] = None) -> None:
    cfg = cfg or ProbabilityConfig()
    conn = get_connection()
    try:
        ensure_probability_columns(conn)

        subject_question_counts = conn.execute(
            """
            SELECT s.id AS subject_id, COUNT(q.id) AS total_questions
            FROM subjects s
            LEFT JOIN pyq_questions q ON q.subject_id = s.id AND q.topic_id IS NOT NULL
            GROUP BY s.id
            """
        ).fetchall()
        total_map = {row["subject_id"]: row["total_questions"] for row in subject_question_counts}

        rows = conn.execute(
            """
            SELECT
                ti.topic_id,
                ti.frequency,
                ti.last_asked_year,
                t.topic_name,
                m.subject_id
            FROM topic_importance ti
            JOIN topics t ON ti.topic_id = t.id
            JOIN modules m ON t.module_id = m.id
            """
        ).fetchall()

        for row in rows:
            total_questions = total_map.get(row["subject_id"], 0) or 1
            frequency_score = (row["frequency"] / total_questions) * 100

            last_year = row["last_asked_year"]
            if last_year is None:
                recency_score = 0
            else:
                gap = max(0, cfg.recent_year - int(last_year))
                if gap == 0:
                    recency_score = 100
                elif gap == 1:
                    recency_score = 80
                elif gap == 2:
                    recency_score = 60
                elif gap == 3:
                    recency_score = 40
                else:
                    recency_score = 20

            probability_score = round(
                (cfg.freq_weight * frequency_score) + (cfg.recency_weight * recency_score),
                2,
            )
            probability_label = classify_probability(probability_score)

            conn.execute(
                """
                UPDATE topic_importance
                SET probability_score = ?, probability_label = ?
                WHERE topic_id = ?
                """,
                (probability_score, probability_label, row["topic_id"]),
            )

        conn.commit()
        print("Probability engine updated successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    build_probability_engine()