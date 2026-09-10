from __future__ import annotations

import pandas as pd
from db import get_db_connection

PYQ_FILE = "data/proceessed/PYQ.xlsx"


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def normalize_subject_code(value) -> str:
    return normalize_text(value).upper()


def safe_int(value):
    try:
        if pd.isna(value):
            return None
        return int(value)
    except Exception:
        return None


def main():
    conn = get_db_connection()
    cur = conn.cursor()

    # rebuild from scratch each run so re-seeding never duplicates rows
    # (this table has no natural UNIQUE constraint to upsert against)
    cur.execute("DELETE FROM pyq_questions")

    df = pd.read_excel(PYQ_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    required_cols = [
        "subject_code",
        "year",
        "exam_type",
        "module_no",
        "marks",
        "question_text",
        "topic_name",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in PYQ file: {missing}")

    inserted = 0
    skipped = 0

    # preload all subject ids by subject_code
    subject_rows = cur.execute(
        """
        SELECT id, subject_code, subject_name, department, semester
        FROM subjects
        """
    ).fetchall()

    subject_map = {}
    for row in subject_rows:
        code = normalize_subject_code(row["subject_code"])
        subject_map.setdefault(code, []).append(row["id"])

    # optional dedupe protection inside this run
    seen = set()

    for _, row in df.iterrows():
        subject_code = normalize_subject_code(row["subject_code"])
        question_text = normalize_text(row["question_text"])
        exam_type = normalize_text(row["exam_type"])
        topic_name = normalize_text(row["topic_name"])

        year = safe_int(row["year"])
        module_no = safe_int(row["module_no"])
        marks = safe_int(row["marks"])

        if not subject_code or not question_text:
            skipped += 1
            continue

        matching_subject_ids = subject_map.get(subject_code, [])
        if not matching_subject_ids:
            skipped += 1
            continue

        # insert same PYQ for all matching subject rows
        for subject_id in matching_subject_ids:
            dedupe_key = (
                subject_id,
                year,
                exam_type.lower(),
                module_no,
                marks,
                question_text.lower(),
                topic_name.lower(),
            )

            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            cur.execute(
                """
                INSERT INTO pyq_questions (
                    subject_id,
                    year,
                    exam_type,
                    module_no,
                    marks,
                    question_text,
                    topic_id,
                    topic_name
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    subject_id,
                    year,
                    exam_type,
                    module_no,
                    marks,
                    question_text,
                    topic_name if topic_name else None,
                ),
            )
            inserted += 1

    conn.commit()
    conn.close()

    print("PYQ seeding completed successfully.")
    print(f"Inserted rows: {inserted}")
    print(f"Skipped rows: {skipped}")


if __name__ == "__main__":
    main()