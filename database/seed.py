from __future__ import annotations

import pandas as pd
from db import get_db_connection

SYLLABUS_FILE = "data/proceessed/syllabus.xlsx"

# Departments you want active in the app
ACTIVE_DEPARTMENTS = ["CSE", "AI&DS", "EEE", "EC", "ME", "CIVIL"]

# Shared/core subjects that should appear in multiple departments
# Add or remove codes based on your actual curriculum
SHARED_SUBJECT_DEPARTMENTS = {
    "CST201": ["CSE", "AI&DS"],   # Data Structures
    "CST204": ["CSE", "AI&DS"],   # DBMS
    "CST205": ["CSE", "AI&DS"],   # OOP in Java
    "CST206": ["CSE", "AI&DS"],   # Operating Systems
    "CST303": ["CSE", "AI&DS"],   # Computer Networks
}

# Semester 1/2 common handling
COMMON_DEPARTMENTS = ACTIVE_DEPARTMENTS


def normalize_department(dep: str) -> str:
    dep = str(dep).strip().upper()
    aliases = {
        "AI & DS": "AI&DS",
        "AIDS": "AI&DS",
        "AI DS": "AI&DS",
        "MECH": "ME",
        "MECHANICAL": "ME",
        "ECE": "EC",
        "ELECTRONICS": "EC",
        "EEE": "EEE",
        "CIVIL ENGINEERING": "CIVIL",
        "COMPUTER SCIENCE": "CSE",
    }
    return aliases.get(dep, dep)


def load_clean_dataframe() -> pd.DataFrame:
    df = pd.read_excel(SYLLABUS_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    required = [
        "scheme", "department", "semester", "subject_code",
        "subject_name", "module_no", "module_title", "topic_name"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in syllabus file: {missing}")

    for col in ["scheme", "department", "subject_code", "subject_name", "module_title", "topic_name"]:
        df[col] = df[col].astype(str).str.strip()

    df["department"] = df["department"].apply(normalize_department)
    df["semester"] = pd.to_numeric(df["semester"], errors="coerce")
    df["module_no"] = pd.to_numeric(df["module_no"], errors="coerce")

    df = df.dropna(subset=["semester", "module_no"]).copy()
    df["semester"] = df["semester"].astype(int)
    df["module_no"] = df["module_no"].astype(int)

    # remove empty text rows
    df = df[
        (df["subject_code"].str.strip() != "") &
        (df["subject_name"].str.strip() != "") &
        (df["module_title"].str.strip() != "") &
        (df["topic_name"].str.strip() != "")
    ].copy()

    return df


def expand_subject_rows(df: pd.DataFrame) -> pd.DataFrame:
    expanded_rows = []

    for _, row in df.iterrows():
        subject_code = row["subject_code"].strip().upper()
        department = normalize_department(row["department"])
        semester = int(row["semester"])

        # 1) COMMON subjects -> duplicate across all active departments
        if department == "COMMON":
            target_departments = COMMON_DEPARTMENTS

        # 2) Shared/core subjects -> duplicate across configured departments
        elif subject_code in SHARED_SUBJECT_DEPARTMENTS:
            target_departments = SHARED_SUBJECT_DEPARTMENTS[subject_code]

        # 3) Normal subject -> keep original department
        else:
            target_departments = [department]

        for dep in target_departments:
            new_row = row.copy()
            new_row["department"] = dep
            expanded_rows.append(new_row)

    out = pd.DataFrame(expanded_rows)

    # remove duplicates after expansion
    out = out.drop_duplicates(
        subset=[
            "scheme", "department", "semester", "subject_code",
            "subject_name", "module_no", "module_title", "topic_name"
        ]
    ).copy()

    return out


def seed_subjects_modules_topics(df: pd.DataFrame) -> None:
    conn = get_db_connection()
    cur = conn.cursor()

    subject_map = {}
    module_map = {}

    # -------------------------
    # Insert subjects
    # -------------------------
    subject_rows = (
        df[["subject_code", "subject_name", "scheme", "department", "semester"]]
        .drop_duplicates()
        .sort_values(["department", "semester", "subject_code"])
    )

    for _, row in subject_rows.iterrows():
        subject_key = (
            row["subject_code"],
            row["scheme"],
            row["department"],
            int(row["semester"]),
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO subjects (
                subject_code, subject_name, scheme, department, semester
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["subject_code"],
                row["subject_name"],
                row["scheme"],
                row["department"],
                int(row["semester"]),
            ),
        )

        cur.execute(
            """
            SELECT id
            FROM subjects
            WHERE subject_code = ?
              AND scheme = ?
              AND department = ?
              AND semester = ?
            """,
            subject_key,
        )
        subject_id = cur.fetchone()["id"]
        subject_map[subject_key] = subject_id

    # -------------------------
    # Insert modules
    # -------------------------
    module_rows = (
        df[[
            "subject_code", "scheme", "department", "semester",
            "module_no", "module_title"
        ]]
        .drop_duplicates()
        .sort_values(["department", "semester", "subject_code", "module_no"])
    )

    for _, row in module_rows.iterrows():
        subject_key = (
            row["subject_code"],
            row["scheme"],
            row["department"],
            int(row["semester"]),
        )
        subject_id = subject_map[subject_key]

        cur.execute(
            """
            INSERT OR IGNORE INTO modules (subject_id, module_no, module_title)
            VALUES (?, ?, ?)
            """,
            (
                subject_id,
                int(row["module_no"]),
                row["module_title"],
            ),
        )

        cur.execute(
            """
            SELECT id
            FROM modules
            WHERE subject_id = ?
              AND module_no = ?
            """,
            (subject_id, int(row["module_no"])),
        )
        module_id = cur.fetchone()["id"]
        module_map[(subject_id, int(row["module_no"]))] = module_id

    # -------------------------
    # Insert topics
    # -------------------------
    topic_rows = (
        df[[
            "subject_code", "scheme", "department", "semester",
            "module_no", "topic_name"
        ]]
        .drop_duplicates()
        .sort_values(["department", "semester", "subject_code", "module_no", "topic_name"])
    )

    inserted_topics = 0

    for _, row in topic_rows.iterrows():
        subject_key = (
            row["subject_code"],
            row["scheme"],
            row["department"],
            int(row["semester"]),
        )
        subject_id = subject_map[subject_key]
        module_id = module_map[(subject_id, int(row["module_no"]))]

        cur.execute(
            """
            INSERT OR IGNORE INTO topics (module_id, topic_name)
            VALUES (?, ?)
            """,
            (
                module_id,
                row["topic_name"],
            ),
        )
        inserted_topics += 1

    conn.commit()

    # summary
    subject_count = cur.execute("SELECT COUNT(*) AS cnt FROM subjects").fetchone()["cnt"]
    module_count = cur.execute("SELECT COUNT(*) AS cnt FROM modules").fetchone()["cnt"]
    topic_count = cur.execute("SELECT COUNT(*) AS cnt FROM topics").fetchone()["cnt"]

    conn.close()

    print("Syllabus seeding completed successfully.")
    print(f"Subjects: {subject_count}")
    print(f"Modules: {module_count}")
    print(f"Topics: {topic_count}")


def main():
    df = load_clean_dataframe()
    expanded_df = expand_subject_rows(df)
    seed_subjects_modules_topics(expanded_df)


if __name__ == "__main__":
    main()