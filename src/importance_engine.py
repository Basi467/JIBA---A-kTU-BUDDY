from __future__ import annotations

import sqlite3

DB_PATH = "database/ktu.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def classify(score: float) -> str:
    if score >= 8:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"

def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    # clear old values
    cur.execute("DELETE FROM topic_importance")

    stats = cur.execute(
        """
        SELECT
            topic_id,
            COUNT(*) AS frequency,
            MAX(year) AS last_asked_year,
            SUM(
                CASE
                    WHEN marks >= 8 THEN 1.5
                    ELSE 1.0
                END
            ) AS weighted_score
        FROM pyq_questions
        WHERE topic_id IS NOT NULL
        GROUP BY topic_id
        """
    ).fetchall()

    print(f"Grouped topic rows found: {len(stats)}")

    inserted = 0

    for row in stats:
        weighted_score = float(row["weighted_score"]) if row["weighted_score"] is not None else 0.0
        importance_level = classify(weighted_score)

        cur.execute(
            """
            INSERT INTO topic_importance (
                topic_id,
                frequency,
                weighted_score,
                importance_level,
                last_asked_year
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["topic_id"],
                row["frequency"],
                weighted_score,
                importance_level,
                row["last_asked_year"],
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()

    print(f"Inserted topic_importance rows: {inserted}")

if __name__ == "__main__":
    main()