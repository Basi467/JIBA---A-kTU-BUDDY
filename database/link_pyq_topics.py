from __future__ import annotations

import sqlite3
from difflib import SequenceMatcher

from db import get_db_path

DB_PATH = get_db_path()


def normalize(s: str) -> str:
    s = str(s).lower().strip()
    s = " ".join(s.split())

    replacements = {
        "b+ tree": "bplus tree",
        "b-tree": "btree",
        "binary search tree": "bst",
        "breadth first search": "bfs",
        "depth first search": "dfs",
        "naive bayes": "naivebayes",
        "decision tree": "decisiontree",
        "f-measure": "fmeasure",
        "f measure": "fmeasure",
        "cross validation": "crossvalidation",
        "round robin": "roundrobin",
        "critical section": "criticalsection",
        "first fit": "firstfit",
        "best fit": "bestfit",
        "worst fit": "worstfit",
    }

    for a, b in replacements.items():
        s = s.replace(a, b)

    return s


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, subject_id, module_no, topic_name
        FROM pyq_questions
        WHERE topic_id IS NULL
          AND topic_name IS NOT NULL
          AND TRIM(topic_name) != ''
        """
    ).fetchall()

    linked_exact = 0
    linked_module_fuzzy = 0
    linked_subject_fuzzy = 0
    unresolved = 0

    for row in rows:
        pyq_id = row["id"]
        subject_id = row["subject_id"]
        module_no = row["module_no"]
        topic_name = row["topic_name"]

        # 1) exact match: subject + module + topic
        exact = None
        if module_no is not None:
            exact = cur.execute(
                """
                SELECT t.id, t.topic_name
                FROM topics t
                JOIN modules m ON t.module_id = m.id
                WHERE m.subject_id = ?
                  AND m.module_no = ?
                  AND LOWER(TRIM(t.topic_name)) = LOWER(TRIM(?))
                LIMIT 1
                """,
                (subject_id, module_no, topic_name),
            ).fetchone()

        if exact:
            cur.execute(
                "UPDATE pyq_questions SET topic_id = ? WHERE id = ?",
                (exact["id"], pyq_id),
            )
            linked_exact += 1
            continue

        # 2) fuzzy match within same subject + module
        best_id = None
        best_score = 0.0

        if module_no is not None:
            module_candidates = cur.execute(
                """
                SELECT t.id, t.topic_name
                FROM topics t
                JOIN modules m ON t.module_id = m.id
                WHERE m.subject_id = ?
                  AND m.module_no = ?
                """,
                (subject_id, module_no),
            ).fetchall()

            for c in module_candidates:
                score = similarity(topic_name, c["topic_name"])
                if score > best_score:
                    best_score = score
                    best_id = c["id"]

            if best_id is not None and best_score >= 0.55:
                cur.execute(
                    "UPDATE pyq_questions SET topic_id = ? WHERE id = ?",
                    (best_id, pyq_id),
                )
                linked_module_fuzzy += 1
                continue

        # 3) fuzzy fallback across whole subject
        best_id = None
        best_score = 0.0

        subject_candidates = cur.execute(
            """
            SELECT t.id, t.topic_name
            FROM topics t
            JOIN modules m ON t.module_id = m.id
            WHERE m.subject_id = ?
            """,
            (subject_id,),
        ).fetchall()

        for c in subject_candidates:
            score = similarity(topic_name, c["topic_name"])
            if score > best_score:
                best_score = score
                best_id = c["id"]

        if best_id is not None and best_score >= 0.68:
            cur.execute(
                "UPDATE pyq_questions SET topic_id = ? WHERE id = ?",
                (best_id, pyq_id),
            )
            linked_subject_fuzzy += 1
        else:
            unresolved += 1

    conn.commit()

    remaining = cur.execute(
        "SELECT COUNT(*) AS cnt FROM pyq_questions WHERE topic_id IS NULL"
    ).fetchone()["cnt"]

    conn.close()

    print(f"Linked exact: {linked_exact}")
    print(f"Linked module fuzzy: {linked_module_fuzzy}")
    print(f"Linked subject fuzzy: {linked_subject_fuzzy}")
    print(f"Still unresolved: {unresolved}")
    print(f"Remaining NULL topic_id: {remaining}")


if __name__ == "__main__":
    main()