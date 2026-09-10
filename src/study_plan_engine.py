from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

DB_PATH = "database/ktu.db"


@dataclass
class StudyPlanItem:
    plan_date: str
    subject_name: str
    module_no: int
    topic_id: int
    topic_name: str
    priority_label: str
    question_count: int
    weighted_score: float
    recommended_hours: float
    priority_score: float


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def priority_weight(label: str) -> float:
    label = (label or "").lower()
    if label == "high":
        return 3.0
    if label == "medium":
        return 2.0
    return 1.0


def fetch_module_topic_priority(subject_name: str, department: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        query = """
            SELECT
                s.subject_name,
                mtp.module_no,
                t.id AS topic_id,
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
        query += """
            ORDER BY
                mtp.module_no,
                CASE mtp.priority_label
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    ELSE 3
                END,
                mtp.weighted_score DESC,
                mtp.question_count DESC,
                t.topic_name
        """

        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def compute_priority(row: sqlite3.Row, weak_topics: List[str]) -> float:
    weak_set = {x.strip().lower() for x in weak_topics}
    topic_name = row["topic_name"].strip().lower()

    score = 0.0
    score += priority_weight(row["priority_label"]) * 3.0
    score += float(row["weighted_score"])
    score += float(row["question_count"]) * 0.5

    if topic_name in weak_set:
        score += 5.0

    return round(score, 2)


def generate_study_plan(
    subject_name: str,
    exam_date_str: str,
    hours_per_day: float,
    weak_topics: Optional[List[str]] = None,
    department: Optional[str] = None,
) -> List[StudyPlanItem]:
    weak_topics = weak_topics or []
    rows = fetch_module_topic_priority(subject_name, department=department)

    if not rows:
        raise ValueError(f"No module-topic priority data found for subject: {subject_name}")

    exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
    today = date.today()
    days_left = (exam_date - today).days

    if days_left <= 0:
        raise ValueError("Exam date must be in the future.")
    if hours_per_day <= 0:
        raise ValueError("Hours per day must be greater than 0.")

    scored_rows = []
    for row in rows:
        priority_score = compute_priority(row, weak_topics)
        scored_rows.append((row, priority_score))

    # Highest-priority topics first
    scored_rows.sort(
        key=lambda x: (
            x[0]["module_no"],
            {"High": 0, "Medium": 1, "Low": 2}.get(x[0]["priority_label"], 3),
            -x[1],
        )
    )

    total_available_hours = days_left * hours_per_day
    total_priority = sum(score for _, score in scored_rows) or 1.0

    plan: List[StudyPlanItem] = []
    current_date = today

    for row, priority_score in scored_rows:
        recommended_hours = max(
            1.0,
            round((priority_score / total_priority) * total_available_hours, 2),
        )

        plan.append(
            StudyPlanItem(
                plan_date=current_date.isoformat(),
                subject_name=row["subject_name"],
                module_no=int(row["module_no"]),
                topic_id=int(row["topic_id"]),
                topic_name=row["topic_name"],
                priority_label=row["priority_label"],
                question_count=int(row["question_count"]),
                weighted_score=float(row["weighted_score"]),
                recommended_hours=recommended_hours,
                priority_score=priority_score,
            )
        )

        current_date += timedelta(days=1)
        if current_date >= exam_date:
            current_date = today

    return plan


if __name__ == "__main__":
    subject_name = "Operating Systems"
    exam_date = "2026-04-20"
    hours_per_day = 3
    weak_topics = ["Deadlock prevention", "Paging"]

    plan = generate_study_plan(
        subject_name=subject_name,
        exam_date_str=exam_date,
        hours_per_day=hours_per_day,
        weak_topics=weak_topics,
    )

    current_module = None
    for item in plan[:20]:
        if item.module_no != current_module:
            current_module = item.module_no
            print(f"\nModule {current_module}")
        print(
            f"{item.plan_date} | {item.topic_name} | "
            f"{item.priority_label} | repeated={item.question_count} | "
            f"{item.recommended_hours} hrs"
        )